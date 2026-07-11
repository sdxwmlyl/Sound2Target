import os
import json
import asyncio
import logging
import requests as http_requests
import time
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from models.video_analysis import VideoAnalysisModel
from models.project import ProjectModel
from core.video.downloader import download_audio
from core.video.transcript_filter import filter_transcript
from core.video.merger import merge_content
from core.video.frame_analyzer import analyze_frame
from core.video.frame_capture import generate_capture_plan
from config.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/video", tags=["video"])


class VideoAnalyzeRequest(BaseModel):
    url: str
    project_name: Optional[str] = None
    summary_prompt: str = ""
    sample_interval: Optional[int] = None
    enable_frame_capture: bool = True
    enable_transcript: bool = True


@router.post("/analyze")
async def analyze_video(request: VideoAnalyzeRequest, background_tasks: BackgroundTasks):
    settings = get_settings()
    interval = request.sample_interval or settings.video.sample_interval

    # Create task record
    task = await asyncio.to_thread(
        VideoAnalysisModel.create,
        url=request.url,
        summary_prompt=request.summary_prompt,
        sample_interval=interval
    )
    task_id = task["id"]

    # Start background processing
    background_tasks.add_task(
        process_video_analysis,
        task_id=task_id,
        url=request.url,
        project_name=request.project_name,
        summary_prompt=request.summary_prompt,
        sample_interval=interval,
        enable_frame_capture=request.enable_frame_capture,
        enable_transcript=request.enable_transcript
    )

    return {"task_id": task_id, "status": "pending", "message": "Video analysis started"}


@router.get("/analyze/{task_id}")
async def get_analysis(task_id: int):
    task = await asyncio.to_thread(VideoAnalysisModel.get_by_id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/tasks")
async def list_tasks(limit: int = 20):
    return await asyncio.to_thread(VideoAnalysisModel.get_all, limit)


async def process_video_analysis(
    task_id: int,
    url: str,
    project_name: Optional[str],
    summary_prompt: str,
    sample_interval: int,
    enable_frame_capture: bool,
    enable_transcript: bool
):
    """后台处理视频分析任务。"""
    try:
        # Step 1: Download audio
        await asyncio.to_thread(
            VideoAnalysisModel.update, task_id, status="downloading"
        )
        audio_info = await asyncio.to_thread(download_audio, url)
        video_title = audio_info["title"]
        video_duration = audio_info["duration"]
        await asyncio.to_thread(
            VideoAnalysisModel.update, task_id,
            video_title=video_title, video_duration=video_duration
        )

        # Step 2: Transcribe
        segments = []
        audio_file_id = None
        project_id = None
        if enable_transcript:
            await asyncio.to_thread(
                VideoAnalysisModel.update, task_id, status="transcribing"
            )

            # Create project
            name = project_name or f"视频分析-{video_title[:30]}"
            project = await asyncio.to_thread(
                ProjectModel.create, name, f"URL: {url}"
            )
            project_id = project.id

            # Upload audio file via internal API
            with open(audio_info["path"], "rb") as f:
                files = {"file": ("audio.wav", f, "audio/wav")}
                data = {"audio_name": video_title[:50]}
                resp = http_requests.post(
                    f"http://localhost:8000/api/projects/{project_id}/upload",
                    files=files, data=data, timeout=60
                )
                resp.raise_for_status()
                upload_result = resp.json()
                audio_file_id = upload_result["id"]

            # Poll for transcription completion (max 10 min)
            for _ in range(120):
                time.sleep(5)
                resp = http_requests.get(
                    f"http://localhost:8000/api/audio-files/{audio_file_id}",
                    timeout=10
                )
                info = resp.json()
                if info["status"] == "completed":
                    break
                elif info["status"] == "failed":
                    raise RuntimeError(
                        f"Transcription failed: {info.get('error_message')}"
                    )
            else:
                raise RuntimeError("Transcription timed out (10 min)")

            # Get transcript segments
            resp = http_requests.get(
                f"http://localhost:8000/api/audio-files/{audio_file_id}/transcript",
                timeout=30
            )
            transcript_data = resp.json()
            segments = transcript_data.get("segments", [])

            await asyncio.to_thread(
                VideoAnalysisModel.update, task_id,
                project_id=project_id,
                audio_file_id=audio_file_id,
                transcript_segments=len(segments)
            )

        # Step 3: Generate capture plan
        capture_plan = []
        if enable_frame_capture and segments:
            await asyncio.to_thread(
                VideoAnalysisModel.update, task_id, status="planning"
            )
            capture_plan = await asyncio.to_thread(
                generate_capture_plan, segments, sample_interval, video_duration
            )
            await asyncio.to_thread(
                VideoAnalysisModel.update, task_id,
                frames_captured=len(capture_plan)
            )

        # Step 4: Analyze frames (if multimodal configured)
        frame_descriptions = []
        if capture_plan:
            settings = get_settings()
            has_key = settings.multimodal.api_key or os.getenv("MULTIMODAL_API_KEY")
            if has_key:
                await asyncio.to_thread(
                    VideoAnalysisModel.update, task_id, status="analyzing_frames"
                )
                for item in capture_plan:
                    try:
                        desc = await asyncio.to_thread(
                            analyze_frame,
                            item.get("frame_path", ""),
                            item["time"]
                        )
                        frame_descriptions.append(desc)
                    except Exception as e:
                        logger.warning(
                            f"Frame analysis failed at {item['time']}s: {e}"
                        )
                await asyncio.to_thread(
                    VideoAnalysisModel.update, task_id,
                    frames_analyzed=len(frame_descriptions)
                )

        # Step 5: Merge content
        await asyncio.to_thread(
            VideoAnalysisModel.update, task_id, status="merging"
        )
        merged = await asyncio.to_thread(
            merge_content, segments, frame_descriptions
        )
        await asyncio.to_thread(
            VideoAnalysisModel.update, task_id, content_items=len(merged)
        )

        # Step 6: Generate summary via LLM
        summary = ""
        if summary_prompt:
            await asyncio.to_thread(
                VideoAnalysisModel.update, task_id, status="summarizing"
            )
            from core.llm import get_llm
            llm = get_llm()

            content_text = json.dumps(merged, ensure_ascii=False, indent=2)[:50000]
            messages = [
                {
                    "role": "system",
                    "content": "你是一位专业的内容分析师。请用中文回答，结构清晰。"
                },
                {
                    "role": "user",
                    "content": (
                        f"用户要求：{summary_prompt}\n\n"
                        f"请基于以下完整内容清单，按用户要求生成结构化总结。\n\n"
                        f"内容清单：\n{content_text}"
                    )
                }
            ]
            summary = await llm.chat(messages, max_tokens=8192)

        # Save final results
        await asyncio.to_thread(
            VideoAnalysisModel.update, task_id,
            status="completed",
            summary=summary,
            merged_content=json.dumps(merged, ensure_ascii=False)
        )
        logger.info(f"Video analysis completed: task_id={task_id}")

    except Exception as e:
        logger.error(f"Video analysis failed (task_id={task_id}): {e}", exc_info=True)
        await asyncio.to_thread(
            VideoAnalysisModel.update, task_id,
            status="failed", error_message=str(e)
        )
