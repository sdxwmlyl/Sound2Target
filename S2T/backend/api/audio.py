import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, Optional
from datetime import datetime

from models.session import SessionModel
from models.audio_file import AudioFileModel
from models.transcript import TranscriptModel
from core.audio import MicrophoneCapture, SystemSoundCapture
from core.asr import get_asr_engine
from config.settings import get_settings


router = APIRouter(prefix="/api/audio", tags=["audio"])

active_connections: Dict[str, WebSocket] = {}
active_captures: Dict[str, object] = {}
audio_buffers: Dict[str, bytearray] = {}


@router.websocket("/ws/{session_id}")
async def websocket_audio(websocket: WebSocket, session_id: str):
    await websocket.accept()
    active_connections[session_id] = websocket
    audio_buffers[session_id] = bytearray()
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "start_capture":
                source_type = message.get("source_type", "microphone")
                hotwords = message.get("hotwords", "")
                
                await start_capture(session_id, source_type, hotwords, websocket)
            
            elif message.get("type") == "audio_data":
                audio_base64 = message.get("audio_data", "")
                if audio_base64:
                    import base64
                    audio_bytes = base64.b64decode(audio_base64)
                    audio_buffers[session_id].extend(audio_bytes)
            
            elif message.get("type") == "stop_capture":
                await stop_capture(session_id, websocket)
            
            elif message.get("type") == "transcribe_buffer":
                hotwords = message.get("hotwords", "")
                await transcribe_buffer(session_id, hotwords, websocket)
    
    except WebSocketDisconnect:
        await cleanup_session(session_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await cleanup_session(session_id)


async def start_capture(session_id: str, source_type: str, hotwords: str, websocket: WebSocket):
    settings = get_settings()
    
    if source_type == "microphone":
        capture = MicrophoneCapture(
            sample_rate=settings.audio.sample_rate,
            chunk_duration=settings.audio.chunk_duration
        )
        capture.start_microphone()
    elif source_type == "system":
        capture = SystemSoundCapture(
            sample_rate=settings.audio.sample_rate,
            chunk_duration=settings.audio.chunk_duration
        )
        capture.start_system_sound()
    else:
        await websocket.send_json({"type": "error", "message": f"Unknown source type: {source_type}"})
        return
    
    active_captures[session_id] = capture
    audio_buffers[session_id] = bytearray()
    
    await websocket.send_json({
        "type": "capture_started",
        "source_type": source_type,
        "timestamp": datetime.now().isoformat()
    })
    
    asyncio.create_task(send_audio_chunks(session_id, capture, websocket))


async def send_audio_chunks(session_id: str, capture, websocket: WebSocket):
    import base64
    
    while session_id in active_captures:
        try:
            audio_base64 = capture.get_audio_base64(timeout=0.5)
            if audio_base64:
                audio_buffers[session_id].extend(base64.b64decode(audio_base64))
                
                await websocket.send_json({
                    "type": "audio_chunk",
                    "audio_data": audio_base64,
                    "buffer_size": len(audio_buffers[session_id])
                })
        except Exception as e:
            print(f"Audio chunk error: {e}")
            break
        
        await asyncio.sleep(0.1)


async def stop_capture(session_id: str, websocket: WebSocket):
    if session_id in active_captures:
        capture = active_captures[session_id]
        capture.stop()
        del active_captures[session_id]
    
    await websocket.send_json({
        "type": "capture_stopped",
        "buffer_size": len(audio_buffers.get(session_id, bytearray())),
        "timestamp": datetime.now().isoformat()
    })


async def transcribe_buffer(session_id: str, hotwords: str, websocket: WebSocket):
    buffer = audio_buffers.get(session_id)
    if not buffer or len(buffer) == 0:
        await websocket.send_json({"type": "error", "message": "No audio data to transcribe"})
        return
    
    try:
        asr_engine = get_asr_engine()
        segments = await asr_engine.transcribe_audio_data(
            bytes(buffer),
            sample_rate=16000,
            hotwords=hotwords
        )
        
        await websocket.send_json({
            "type": "transcript_result",
            "segments": segments,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})


async def cleanup_session(session_id: str):
    if session_id in active_connections:
        del active_connections[session_id]
    
    if session_id in active_captures:
        capture = active_captures[session_id]
        capture.stop()
        del active_captures[session_id]
    
    if session_id in audio_buffers:
        del audio_buffers[session_id]


@router.get("/devices")
async def list_audio_devices():
    import sounddevice as sd
    devices = sd.query_devices()
    
    input_devices = []
    for i, d in enumerate(devices):
        if d['max_input_channels'] > 0:
            is_cable = 'CABLE' in d['name'].upper()
            input_devices.append({
                "id": i,
                "name": d['name'],
                "is_cable": is_cable,
                "channels": d['max_input_channels']
            })
    
    return {"devices": input_devices}