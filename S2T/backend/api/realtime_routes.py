import json
import asyncio
import logging
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query

from core.realtime import handle_realtime_websocket, realtime_manager

router = APIRouter(prefix="/api/realtime", tags=["realtime"])
logger = logging.getLogger(__name__)


@router.websocket("/ws/{project_id}")
async def realtime_ws(websocket: WebSocket, project_id: int, session_id: str = Query(...)):
    await handle_realtime_websocket(websocket, session_id, project_id)


@router.get("/sessions")
async def list_active_sessions():
    return {"sessions": realtime_manager.get_active_sessions()}


@router.get("/sessions/{session_id}")
async def get_session_status(session_id: str):
    session = realtime_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session.session_id,
        "project_id": session.project_id,
        "is_recording": session.is_recording,
        "source_type": session.source_type,
        "audio_file_id": session.audio_file_id,
        "buffer_duration": session.get_buffer_duration(),
        "started_at": session.started_at.isoformat() if session.started_at else None
    }