import os
import tempfile
from pydub import AudioSegment


def get_audio_duration(filepath: str) -> float:
    """获取音频时长，优先 pydub，失败用 ffprobe 兜底"""
    try:
        audio = AudioSegment.from_file(filepath)
        dur = len(audio) / 1000.0
        if dur > 0:
            return dur
    except Exception:
        pass
    
    # pydub 失败，尝试 ffprobe
    try:
        import subprocess, json
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", filepath],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            info = json.loads(result.stdout)
            dur = float(info.get("format", {}).get("duration", 0))
            if dur > 0:
                return dur
    except Exception:
        pass
    
    # 最后尝试 soundfile
    try:
        import soundfile as sf
        info = sf.info(filepath)
        return info.duration
    except Exception:
        pass
    
    return 0.0


def convert_to_wav(filepath: str, sample_rate: int = 16000) -> str:
    ext = filepath.split('.')[-1].lower()
    
    if ext == 'wav':
        try:
            audio = AudioSegment.from_file(filepath)
            if audio.frame_rate == sample_rate and audio.channels == 1:
                return filepath
        except:
            pass
    
    try:
        audio = AudioSegment.from_file(filepath)
        audio = audio.set_frame_rate(sample_rate).set_channels(1).normalize()
        
        temp_path = tempfile.mktemp(suffix='.wav')
        audio.export(temp_path, format='wav')
        
        return temp_path
    except Exception as e:
        print(f"Error converting audio: {e}")
        raise


def format_timestamp(seconds: float) -> str:
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


def merge_segments(segments: list, max_gap: float = 2.0) -> list:
    if not segments:
        return segments
    
    merged = [segments[0]]
    
    for seg in segments[1:]:
        last = merged[-1]
        gap = seg['start_time'] - last['end_time']
        
        if gap <= max_gap and seg['speaker_id'] == last['speaker_id']:
            last['end_time'] = seg['end_time']
            last['text'] += ' ' + seg['text']
        else:
            merged.append(seg)
    
    return merged