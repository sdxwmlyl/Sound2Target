import json
import asyncio
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

from core.realtime import realtime_manager


async def handle_realtime_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    session = realtime_manager.create_session(session_id, websocket)
    
    try:
        await session.send_message("connected", {"session_id": session_id})
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            msg_type = message.get("type")
            
            if msg_type == "ping":
                await session.send_message("pong", {})
            
            elif msg_type == "start_recording":
                source_type = message.get("source_type", "microphone")
                hotwords = message.get("hotwords", "")
                audio_name = message.get("audio_name", "")
                await realtime_manager.start_recording(session_id, source_type, hotwords, audio_name)
            
            elif msg_type == "stop_recording":
                await realtime_manager.stop_recording(session_id)
            
            elif msg_type == "audio_data":
                audio_base64 = message.get("audio_data", "")
                if audio_base64:
                    session.add_audio_data(audio_base64)
                    await session.send_message("audio_received", {
                        "buffer_size": len(session.audio_buffer),
                        "buffer_duration": session.get_buffer_duration()
                    })
            
            elif msg_type == "set_hotwords":
                session.hotwords = message.get("hotwords", "")
                await session.send_message("hotwords_updated", {"hotwords": session.hotwords})
            
            elif msg_type == "get_status":
                await session.send_message("status", {
                    "is_recording": session.is_recording,
                    "buffer_duration": session.get_buffer_duration(),
                    "source_type": session.source_type
                })
    
    except WebSocketDisconnect:
        realtime_manager.remove_session(session_id)
    
    except Exception as e:
        print(f"WebSocket error: {e}")
        realtime_manager.remove_session(session_id)


def get_active_realtime_sessions():
    return realtime_manager.get_active_sessions()