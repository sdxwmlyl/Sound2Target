import os
import uuid
import asyncio
import logging
import aiofiles
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

from models.session import SessionModel, Session
from models.audio_file import AudioFileModel, AudioFile
from models.transcript import TranscriptModel
from models.hotwords import HotwordModel
from config.settings import get_settings
from core.asr import get_asr_engine
from utils.audio_utils import get_audio_duration, convert_to_wav


router = APIRouter(prefix="/api", tags=["transcribe"])


class TranscribeRequest(BaseModel):
    audio_file_id: int
    hotwords: Optional[str] = None
    enable_diarization: bool = True


class TranscriptUpdate(BaseModel):
    text: str


@router.post("/sessions/{session_id}/upload")
async def upload_audio(
    session_id: int,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    session = SessionModel.get_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    settings = get_settings()
    upload_dir = Path(settings.storage.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in settings.audio.supported_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {file_ext}. Supported: {settings.audio.supported_formats}"
        )
    
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    save_path = upload_dir / unique_filename
    
    async with aiofiles.open(save_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    file_size = len(content)
    duration = get_audio_duration(str(save_path))
    
    audio_file = AudioFileModel.create(
        session_id=session_id,
        filename=file.filename,
        filepath=str(save_path),
        duration=duration,
        file_size=file_size
    )
    
    return {
        "id": audio_file.id,
        "filename": audio_file.filename,
        "filepath": audio_file.filepath,
        "duration": audio_file.duration,
        "file_size": audio_file.file_size,
        "status": audio_file.status
    }


@router.post("/transcribe")
async def start_transcribe(request: TranscribeRequest, background_tasks: BackgroundTasks):
    audio_file = AudioFileModel.get_by_id(request.audio_file_id)
    if not audio_file:
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    if audio_file.status == "processing":
        raise HTTPException(status_code=400, detail="Audio file is already being processed")
    
    AudioFileModel.update_status(request.audio_file_id, "processing")
    
    background_tasks.add_task(
        process_transcribe,
        request.audio_file_id,
        request.hotwords,
        request.enable_diarization
    )
    
    return {"message": "Transcription started", "audio_file_id": request.audio_file_id}


async def process_transcribe(audio_file_id: int, hotwords: str, enable_diarization: bool):
    try:
        audio_file = await asyncio.to_thread(AudioFileModel.get_by_id, audio_file_id)
        if not audio_file:
            return
        
        wav_path = await asyncio.to_thread(convert_to_wav, audio_file.filepath)
        
        asr_engine = get_asr_engine()
        segments = await asr_engine.transcribe(wav_path, hotwords or "", enable_diarization)
        
        if wav_path != audio_file.filepath and os.path.exists(wav_path):
            os.remove(wav_path)
        
        await asyncio.to_thread(TranscriptModel.delete_by_audio_file, audio_file_id)
        
        segment_dicts = [
            {
                'audio_file_id': audio_file_id,
                'speaker_id': seg['speaker_id'],
                'start_time': seg['start_time'],
                'end_time': seg['end_time'],
                'text': seg['text']
            }
            for seg in segments
        ]
        await asyncio.to_thread(TranscriptModel.create_batch, segment_dicts)
        
        await asyncio.to_thread(AudioFileModel.update_status, audio_file_id, "completed")
        logger.info(f"Transcription completed for {audio_file_id}")
        
    except Exception as e:
        await asyncio.to_thread(AudioFileModel.update_status, audio_file_id, "failed", str(e))
        logger.error(f"Transcribe error for {audio_file_id}: {e}")


@router.get("/audio-files/{audio_file_id}/transcript")
async def get_transcript(audio_file_id: int):
    audio_file = AudioFileModel.get_by_id(audio_file_id)
    if not audio_file:
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    segments = TranscriptModel.get_by_audio_file(audio_file_id)
    
    return {
        "audio_file": {
            "id": audio_file.id,
            "filename": audio_file.filename,
            "status": audio_file.status,
            "duration": audio_file.duration
        },
        "segments": [
            {
                "id": s.id,
                "speaker_id": s.speaker_id,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "text": s.text,
                "original_text": s.original_text,
                "edited": s.edited_at is not None
            }
            for s in segments
        ]
    }


@router.put("/transcript-segments/{segment_id}")
async def update_segment(segment_id: int, data: TranscriptUpdate):
    segment = TranscriptModel.get_by_id(segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    
    updated = TranscriptModel.update_text(segment_id, data.text)
    return {
        "id": updated.id,
        "text": updated.text,
        "original_text": updated.original_text,
        "edited_at": updated.edited_at
    }


@router.get("/audio-files/{audio_file_id}")
async def get_audio_file(audio_file_id: int):
    audio_file = AudioFileModel.get_by_id(audio_file_id)
    if not audio_file:
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return {
        "id": audio_file.id,
        "filename": audio_file.filename,
        "filepath": audio_file.filepath,
        "duration": audio_file.duration,
        "file_size": audio_file.file_size,
        "status": audio_file.status,
        "error_message": audio_file.error_message
    }


@router.get("/sessions/{session_id}/audio-files")
async def get_session_audio_files(session_id: int):
    session = SessionModel.get_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    audio_files = AudioFileModel.get_by_session(session_id)
    
    return [
        {
            "id": a.id,
            "filename": a.filename,
            "duration": a.duration,
            "file_size": a.file_size,
            "status": a.status,
            "created_at": a.created_at,
            "error_message": a.error_message
        }
        for a in audio_files
    ]