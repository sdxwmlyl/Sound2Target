import os
import uuid
import json
import asyncio
import logging
import subprocess
import aiofiles
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel

from models.project import ProjectModel, Project
from models.audio_file import AudioFileModel, AudioFile
from models.transcript import TranscriptModel
from config.settings import get_settings
from core.asr import get_asr_engine
from utils.audio_utils import get_audio_duration, convert_to_wav

router = APIRouter(prefix="/api", tags=["projects"])
logger = logging.getLogger(__name__)


class ProjectCreate(BaseModel):
    name: str
    description: str = ""


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class HotwordsUpdate(BaseModel):
    hotwords: str


class DownloadUrlRequest(BaseModel):
    url: str
    audio_name: Optional[str] = None


class SegmentUpdate(BaseModel):
    text: str


class AudioUploadResponse(BaseModel):
    id: int
    audio_name: str
    filename: str
    filepath: str
    source_type: str
    duration: Optional[float]
    file_size: Optional[int]
    status: str


@router.get("/projects", response_model=List[dict])
async def list_projects():
    projects = ProjectModel.get_all()
    result = []
    for p in projects:
        audio_files = AudioFileModel.get_by_project(p.id)
        completed_count = len([a for a in audio_files if a.status == 'completed'])
        result.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "hotwords": p.hotwords,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "audio_count": len(audio_files),
            "completed_count": completed_count
        })
    return result


@router.post("/projects", response_model=dict)
async def create_project(data: ProjectCreate):
    project = ProjectModel.create(data.name, data.description)
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "hotwords": project.hotwords
    }


@router.get("/projects/{project_id}", response_model=dict)
async def get_project(project_id: int):
    project = ProjectModel.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    audio_files = AudioFileModel.get_by_project(project_id)
    
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "hotwords": project.hotwords,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "audio_files": [
            {
                "id": a.id,
                "audio_name": a.audio_name,
                "filename": a.filename,
                "source_type": a.source_type,
                "duration": a.duration,
                "status": a.status,
                "created_at": a.created_at
            }
            for a in audio_files
        ]
    }


@router.put("/projects/{project_id}", response_model=dict)
async def update_project(project_id: int, data: ProjectUpdate):
    project = ProjectModel.update(project_id, data.name, data.description)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "hotwords": project.hotwords
    }


@router.put("/projects/{project_id}/hotwords")
async def update_hotwords(project_id: int, data: HotwordsUpdate):
    project = ProjectModel.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    ProjectModel.update(project_id, hotwords=data.hotwords)
    return {"hotwords": data.hotwords}


@router.delete("/projects/{project_id}")
async def delete_project(project_id: int):
    if not ProjectModel.delete(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted"}


@router.get("/projects/{project_id}/audio-files")
async def list_audio_files(project_id: int):
    project = ProjectModel.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    audio_files = AudioFileModel.get_by_project(project_id)
    
    result = []
    for a in audio_files:
        segments = TranscriptModel.get_by_audio_file(a.id)
        char_count = sum(len(s.text) for s in segments)
        result.append({
            "id": a.id,
            "audio_name": a.audio_name,
            "filename": a.filename,
            "source_type": a.source_type,
            "duration": a.duration,
            "file_size": a.file_size,
            "status": a.status,
            "error_message": a.error_message,
            "char_count": char_count,
            "created_at": a.created_at
        })
    
    return result


@router.post("/projects/{project_id}/upload")
async def upload_audio(
    project_id: int,
    file: UploadFile = File(...),
    audio_name: str = Form(""),
    background_tasks: BackgroundTasks = None
):
    project = ProjectModel.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
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
    duration = await asyncio.to_thread(get_audio_duration, str(save_path))
    
    audio_file = AudioFileModel.create(
        project_id=project_id,
        audio_name=audio_name,
        filename=file.filename,
        filepath=str(save_path),
        source_type="file",
        duration=duration,
        file_size=file_size
    )
    
    background_tasks.add_task(
        process_transcribe,
        audio_file.id,
        project.hotwords or ""
    )
    
    return {
        "id": audio_file.id,
        "audio_name": audio_file.audio_name,
        "filename": audio_file.filename,
        "source_type": audio_file.source_type,
        "duration": audio_file.duration,
        "file_size": audio_file.file_size,
        "status": audio_file.status
    }


@router.post("/projects/{project_id}/download-url")
async def download_url_audio(
    project_id: int,
    data: DownloadUrlRequest,
    background_tasks: BackgroundTasks
):
    """通过URL下载音频并自动转写（支持视频平台链接，仅提取音频）"""
    project = ProjectModel.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    settings = get_settings()
    upload_dir = Path(settings.storage.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Use yt-dlp to download audio
    filename_base = f"url_{uuid.uuid4().hex[:8]}"
    output_template = str(upload_dir / f"{filename_base}.%(ext)s")

    yt_dlp_path = settings.video.yt_dlp_path
    cmd = [
        yt_dlp_path,
        "-x", "--audio-format", "wav",
        "-o", output_template,
        "--print-json",
        "--no-playlist",
        "--no-warnings",
        data.url
    ]

    try:
        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, timeout=300
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Download timed out (5 min)")

    if result.returncode != 0:
        error_msg = result.stderr[:300] if result.stderr else "Unknown error"
        raise HTTPException(status_code=400, detail=f"yt-dlp failed: {error_msg}")

    # Parse JSON metadata from stdout
    info = {}
    for line in result.stdout.strip().split('\n'):
        line = line.strip()
        if line.startswith('{'):
            try:
                info = json.loads(line)
            except json.JSONDecodeError:
                continue

    video_title = info.get("title", data.url[:50])
    audio_name = data.audio_name or video_title[:80]

    # Find the downloaded file
    wav_path = upload_dir / f"{filename_base}.wav"
    if not wav_path.exists():
        # Try other extensions yt-dlp might have left
        for ext in ("m4a", "opus", "webm", "mp3", "ogg"):
            candidate = upload_dir / f"{filename_base}.{ext}"
            if candidate.exists():
                wav_path = candidate
                break

    if not wav_path.exists():
        raise HTTPException(status_code=500, detail="Downloaded file not found on disk")

    file_size = wav_path.stat().st_size
    duration = await asyncio.to_thread(get_audio_duration, str(wav_path))

    audio_file = AudioFileModel.create(
        project_id=project_id,
        audio_name=audio_name,
        filename=wav_path.name,
        filepath=str(wav_path),
        source_type="url",
        duration=duration,
        file_size=file_size
    )

    background_tasks.add_task(
        process_transcribe,
        audio_file.id,
        project.hotwords or ""
    )

    return {
        "id": audio_file.id,
        "audio_name": audio_file.audio_name,
        "filename": audio_file.filename,
        "source_type": "url",
        "duration": audio_file.duration,
        "file_size": audio_file.file_size,
        "status": audio_file.status
    }


@router.get("/audio-files/{audio_file_id}")
async def get_audio_file(audio_file_id: int):
    audio_file = AudioFileModel.get_by_id(audio_file_id)
    if not audio_file:
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    segments = TranscriptModel.get_by_audio_file(audio_file_id)
    char_count = sum(len(s.text) for s in segments)
    
    return {
        "id": audio_file.id,
        "project_id": audio_file.project_id,
        "audio_name": audio_file.audio_name,
        "filename": audio_file.filename,
        "filepath": audio_file.filepath,
        "source_type": audio_file.source_type,
        "duration": audio_file.duration,
        "file_size": audio_file.file_size,
        "status": audio_file.status,
        "error_message": audio_file.error_message,
        "char_count": char_count,
        "created_at": audio_file.created_at
    }


@router.get("/audio-files/{audio_file_id}/transcript")
async def get_transcript(audio_file_id: int):
    audio_file = AudioFileModel.get_by_id(audio_file_id)
    if not audio_file:
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    segments = TranscriptModel.get_by_audio_file(audio_file_id)
    
    return {
        "audio_file": {
            "id": audio_file.id,
            "audio_name": audio_file.audio_name,
            "filename": audio_file.filename,
            "source_type": audio_file.source_type,
            "duration": audio_file.duration,
            "status": audio_file.status,
            "summary": audio_file.summary
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
async def update_segment(segment_id: int, data: SegmentUpdate):
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


@router.post("/audio-files/{audio_file_id}/stop")
async def stop_audio(audio_file_id: int):
    audio_file = AudioFileModel.get_by_id(audio_file_id)
    if not audio_file:
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    if audio_file.status == "processing":
        AudioFileModel.update_status(audio_file_id, "stopped")
        return {"message": "Audio processing stopped"}
    
    return {"message": "Audio is not processing"}


@router.delete("/audio-files/{audio_file_id}")
async def delete_audio(audio_file_id: int):
    audio_file = AudioFileModel.get_by_id(audio_file_id)
    if not audio_file:
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    if audio_file.filepath and os.path.exists(audio_file.filepath):
        os.remove(audio_file.filepath)
    
    AudioFileModel.delete(audio_file_id)
    return {"message": "Audio file deleted"}


async def process_transcribe(audio_file_id: int, hotwords: str, retry_count: int = 0, max_retries: int = 30):
    """转写任务，支持ASR占用时自动重试（最多等2.5分钟）"""
    try:
        audio_file = await asyncio.to_thread(AudioFileModel.get_by_id, audio_file_id)
        if not audio_file:
            return
        
        # 已被手动停止或删除，不再重试
        if audio_file.status in ("stopped", "deleted"):
            logger.info(f"Transcribe skipped for {audio_file_id}: status={audio_file.status}")
            return
        
        await asyncio.to_thread(AudioFileModel.update_status, audio_file_id, "processing")
        
        wav_path = await asyncio.to_thread(convert_to_wav, audio_file.filepath)
        
        asr_engine = get_asr_engine()
        
        # 进度回调
        def on_progress(progress):
            logger.info(f"Transcription progress for {audio_file_id}: {progress}")
        
        segments = await asr_engine.transcribe(
            wav_path, 
            hotwords or "", 
            True,
            progress_callback=on_progress
        )
        
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
        
    except RuntimeError as e:
        # ASR被占用，自动重试
        if retry_count < max_retries:
            logger.info(f"ASR busy for {audio_file_id}, retry {retry_count+1}/{max_retries} in 5s...")
            await asyncio.to_thread(AudioFileModel.update_status, audio_file_id, "pending")
            await asyncio.sleep(5)
            # 重新入队：用新的coroutine避免栈溢出
            asyncio.get_event_loop().call_soon(
                lambda: asyncio.ensure_future(
                    process_transcribe(audio_file_id, hotwords, retry_count + 1, max_retries)
                )
            )
        else:
            logger.error(f"Transcribe gave up for {audio_file_id} after {max_retries} retries")
            await asyncio.to_thread(AudioFileModel.update_status, audio_file_id, "failed", "ASR timeout")
    except Exception as e:
        await asyncio.to_thread(AudioFileModel.update_status, audio_file_id, "failed", str(e))
        logger.error(f"Transcribe error for {audio_file_id}: {e}")


@router.get("/audio-files/{audio_file_id}/stream")
async def stream_audio(audio_file_id: int):
    """音频文件流式传输"""
    from fastapi.responses import FileResponse
    
    audio_file = AudioFileModel.get_by_id(audio_file_id)
    if not audio_file:
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    if not audio_file.filepath or not os.path.exists(audio_file.filepath):
        raise HTTPException(status_code=404, detail="Audio file not found on disk")
    
    return FileResponse(
        audio_file.filepath,
        media_type="audio/mpeg",
        filename=audio_file.filename
    )


@router.get("/audio/devices")
async def list_audio_devices():
    """获取音频设备列表"""
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


@router.get("/statistics")
async def get_statistics():
    """获取系统统计信息"""
    projects = ProjectModel.get_all()
    
    total_projects = len(projects)
    total_sessions = 0
    total_audio_files = 0
    total_segments = 0
    completed_files = 0
    failed_files = 0
    total_duration = 0
    
    for project in projects:
        audio_files = AudioFileModel.get_by_project(project.id)
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
        'total_audio_files': total_audio_files,
        'total_segments': total_segments,
        'completed_files': completed_files,
        'failed_files': failed_files,
        'pending_files': total_audio_files - completed_files - failed_files,
        'total_duration_hours': round(total_duration / 3600, 2)
    }