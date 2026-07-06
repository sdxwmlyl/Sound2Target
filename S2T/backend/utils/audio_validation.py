import os
import logging
from pathlib import Path
from typing import List, Optional
from pydub import AudioSegment


logger = logging.getLogger(__name__)


def validate_audio_file(filepath: str) -> tuple[bool, str]:
    """
    验证音频文件是否有效
    
    Returns:
        (is_valid, error_message)
    """
    if not os.path.exists(filepath):
        return False, "文件不存在"
    
    try:
        audio = AudioSegment.from_file(filepath)
        
        if len(audio) == 0:
            return False, "音频时长为0"
        
        return True, ""
        
    except Exception as e:
        return False, f"无法解析音频: {str(e)}"


def get_audio_info(filepath: str) -> dict:
    """
    获取音频文件详细信息
    """
    try:
        audio = AudioSegment.from_file(filepath)
        
        return {
            'duration': len(audio) / 1000.0,
            'channels': audio.channels,
            'sample_rate': audio.frame_rate,
            'bit_depth': audio.sample_width * 8,
            'file_size': os.path.getsize(filepath)
        }
    except Exception as e:
        logger.error(f"Get audio info error: {e}")
        return {}


def normalize_audio(filepath: str, output_path: str = None, target_db: float = -20.0) -> str:
    """
    音频标准化
    """
    try:
        audio = AudioSegment.from_file(filepath)
        audio = audio.normalize(target_db)
        
        if output_path is None:
            output_path = filepath
        
        audio.export(output_path, format="wav")
        return output_path
    except Exception as e:
        logger.error(f"Normalize audio error: {e}")
        raise


def split_audio(filepath: str, chunk_duration: int = 300) -> List[str]:
    """
    将长音频分割成多个片段（用于大文件处理）
    
    Args:
        filepath: 音频文件路径
        chunk_duration: 每个片段的最大时长（秒）
    
    Returns:
        分割后的文件路径列表
    """
    import tempfile
    
    try:
        audio = AudioSegment.from_file(filepath)
        total_duration = len(audio) / 1000.0
        
        if total_duration <= chunk_duration:
            return [filepath]
        
        chunks = []
        start = 0
        
        while start < total_duration:
            end = min(start + chunk_duration, total_duration)
            chunk = audio[start * 1000:end * 1000]
            
            chunk_path = tempfile.mktemp(suffix='.wav')
            chunk.export(chunk_path, format='wav')
            chunks.append(chunk_path)
            
            start = end
        
        return chunks
        
    except Exception as e:
        logger.error(f"Split audio error: {e}")
        return [filepath]


def merge_transcript_results(results: List[dict], offset: float = 0.0) -> List[dict]:
    """
    合合分割音频的转写结果
    """
    merged = []
    
    for i, segments in enumerate(results):
        chunk_offset = offset + i * 300.0
        
        for seg in segments:
            merged.append({
                'speaker_id': seg['speaker_id'],
                'start_time': seg['start_time'] + chunk_offset,
                'end_time': seg['end_time'] + chunk_offset,
                'text': seg['text']
            })
    
    return merged