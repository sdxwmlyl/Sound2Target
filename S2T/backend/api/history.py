import os
import asyncio
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from models.project import ProjectModel
from models.session import SessionModel
from models.audio_file import AudioFileModel
from models.transcript import TranscriptModel
from models.hotwords import HotwordModel
from config.settings import get_settings


router = APIRouter(prefix="/api", tags=["history"])
logger = logging.getLogger(__name__)


class TranscribeHistory(BaseModel):
    project_name: str
    session_name: str
    audio_filename: str
    audio_file_id: int
    duration: float
    segments_count: int
    speakers_count: int
    status: str
    created_at: str


@router.get("/history")
async def get_transcribe_history(
    project_id: Optional[int] = Query(None),
    limit: int = Query(20, ge=1, le=100)
):
    """
    获取转写历史记录
    """
    history = []
    
    if project_id:
        projects = [ProjectModel.get_by_id(project_id)]
    else:
        projects = ProjectModel.get_all()
    
    for project in projects:
        if not project:
            continue
        
        sessions = SessionModel.get_by_project(project.id)
        
        for session in sessions:
            audio_files = AudioFileModel.get_by_session(session.id)
            
            for audio in audio_files:
                segments = TranscriptModel.get_by_audio_file(audio.id)
                speakers = set(s.speaker_id for s in segments)
                
                history.append({
                    'project_name': project.name,
                    'session_name': session.name,
                    'audio_filename': audio.filename,
                    'audio_file_id': audio.id,
                    'duration': audio.duration or 0,
                    'segments_count': len(segments),
                    'speakers_count': len(speakers),
                    'status': audio.status,
                    'created_at': audio.created_at
                })
    
    history.sort(key=lambda x: x['created_at'], reverse=True)
    
    return history[:limit]


@router.get("/statistics")
async def get_statistics():
    """
    获取系统统计信息
    """
    projects = ProjectModel.get_all()
    
    total_projects = len(projects)
    total_sessions = 0
    total_audio_files = 0
    total_segments = 0
    completed_files = 0
    failed_files = 0
    total_duration = 0
    
    for project in projects:
        sessions = SessionModel.get_by_project(project.id)
        total_sessions += len(sessions)
        
        for session in sessions:
            audio_files = AudioFileModel.get_by_session(session.id)
            total_audio_files += len(audio_files)
            
            for audio in audio_files:
                total_duration += audio.duration or 0
                
                if audio.status == 'completed':
                    completed_files += 1
                    segments = TranscriptModel.get_by_audio_file(audio.id)
                    total_segments += len(segments)
                elif audio.status == 'failed':
                    failed_files += 1
    
    return {
        'total_projects': total_projects,
        'total_sessions': total_sessions,
        'total_audio_files': total_audio_files,
        'total_segments': total_segments,
        'completed_files': completed_files,
        'failed_files': failed_files,
        'pending_files': total_audio_files - completed_files - failed_files,
        'total_duration_hours': round(total_duration / 3600, 2)
    }


@router.get("/search")
async def search_transcripts(keyword: str, limit: int = Query(10)):
    """
    搜索转写内容
    """
    if not keyword or len(keyword) < 2:
        raise HTTPException(status_code=400, detail="关键词至少2个字符")
    
    from models.database import get_db
    
    results = []
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT ts.id, ts.text, ts.speaker_id, ts.start_time, ts.end_time,
                      af.id as audio_file_id, af.filename, s.name as session_name,
                      p.name as project_name
               FROM transcript_segments ts
               JOIN audio_files af ON ts.audio_file_id = af.id
               JOIN sessions s ON af.session_id = s.id
               JOIN projects p ON s.project_id = p.id
               WHERE ts.text LIKE ?
               ORDER BY ts.start_time""",
            (f'%{keyword}%',)
        )
        
        rows = cursor.fetchall()
        
        for row in rows[:limit]:
            results.append({
                'segment_id': row[0],
                'text': row[1],
                'speaker_id': row[2],
                'start_time': row[3],
                'end_time': row[4],
                'audio_file_id': row[5],
                'filename': row[6],
                'session_name': row[7],
                'project_name': row[8]
            })
    
    return results