import subprocess
import json
import os
import uuid
import logging
from pathlib import Path
from config.settings import get_settings

logger = logging.getLogger(__name__)


def download_audio(url: str, output_dir: str = None) -> dict:
    """下载视频音频，返回 {"path": str, "title": str, "duration": float}"""
    settings = get_settings()
    if output_dir is None:
        output_dir = settings.video.temp_dir

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    filename = f"video_audio_{uuid.uuid4().hex[:8]}"
    output_path = os.path.join(output_dir, f"{filename}.%(ext)s")

    cmd = [
        settings.video.yt_dlp_path,
        "-x", "--audio-format", "wav",
        "-o", output_path,
        "--print-json",
        "--no-playlist",
        url
    ]

    logger.info(f"Downloading audio from: {url}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        error_msg = result.stderr[:500] if result.stderr else "Unknown error"
        raise RuntimeError(f"yt-dlp failed: {error_msg}")

    # Parse JSON output to get title and duration (last JSON object in stdout)
    info = {}
    for line in result.stdout.strip().split('\n'):
        line = line.strip()
        if line.startswith('{'):
            try:
                info = json.loads(line)
            except json.JSONDecodeError:
                continue

    # Find the actual output file
    wav_path = os.path.join(output_dir, f"{filename}.wav")
    if not os.path.exists(wav_path):
        # yt-dlp may output m4a first then convert; look for any matching file
        for ext in ("m4a", "opus", "webm", "mp3"):
            candidate = os.path.join(output_dir, f"{filename}.{ext}")
            if os.path.exists(candidate):
                wav_path = candidate
                break

    if not os.path.exists(wav_path):
        raise RuntimeError(f"Downloaded audio file not found: {wav_path}")

    logger.info(f"Audio downloaded: {wav_path} ({info.get('title', 'Unknown')})")
    return {
        "path": wav_path,
        "title": info.get("title", "Unknown"),
        "duration": info.get("duration", 0)
    }
