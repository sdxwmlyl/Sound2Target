import json
import asyncio
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect


router = APIRouter(tags=["websocket"])

active_connections: Dict[str, WebSocket] = {}


@router.websocket("/ws/audio/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    active_connections[session_id] = websocket
    
    try:
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await handle_message(websocket, session_id, message)
    
    except WebSocketDisconnect:
        if session_id in active_connections:
            del active_connections[session_id]
        print(f"WebSocket disconnected: {session_id}")
    
    except Exception as e:
        print(f"WebSocket error: {e}")
        if session_id in active_connections:
            del active_connections[session_id]


async def handle_message(websocket: WebSocket, session_id: str, message: dict):
    msg_type = message.get("type")
    
    if msg_type == "ping":
        await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
    
    elif msg_type == "audio_data":
        await handle_audio_data(websocket, session_id, message)
    
    else:
        await websocket.send_json({
            "type": "echo",
            "original": message,
            "timestamp": datetime.now().isoformat()
        })


async def handle_audio_data(websocket: WebSocket, session_id: str, message: dict):
    from api.audio import audio_buffers
    
    audio_base64 = message.get("audio_data", "")
    if not audio_base64:
        return
    
    import base64
    audio_bytes = base64.b64decode(audio_base64)
    
    if session_id not in audio_buffers:
        audio_buffers[session_id] = bytearray()
    
    audio_buffers[session_id].extend(audio_bytes)
    
    await websocket.send_json({
        "type": "audio_received",
        "buffer_size": len(audio_buffers[session_id]),
        "timestamp": datetime.now().isoformat()
    })