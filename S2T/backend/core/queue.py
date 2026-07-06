import os
import asyncio
import logging
from datetime import datetime
from typing import List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TranscribeQueue:
    _instance = None
    _queue: asyncio.Queue = None
    _processing: dict = {}
    _semaphore: asyncio.Semaphore = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def init(self, max_concurrent: int = 2):
        self._queue = asyncio.Queue()
        self._semaphore = asyncio.Semaphore(max_concurrent)
    
    async def add_task(self, audio_file_id: int, hotwords: str = ""):
        if self._queue is None:
            self.init()
        
        task = {
            'audio_file_id': audio_file_id,
            'hotwords': hotwords,
            'added_at': datetime.now().isoformat()
        }
        await self._queue.put(task)
        return task
    
    def get_queue_size(self) -> int:
        if self._queue is None:
            return 0
        return self._queue.qsize()
    
    def get_processing_count(self) -> int:
        return len(self._processing)
    
    async def process_queue(self):
        if self._queue is None:
            self.init()
        
        while True:
            try:
                task = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                
                audio_file_id = task['audio_file_id']
                self._processing[audio_file_id] = task
                
                await self._process_task(task)
                
                del self._processing[audio_file_id]
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Queue processing error: {e}")
    
    async def _process_task(self, task):
        from models.audio_file import AudioFileModel
        from models.transcript import TranscriptModel
        from core.asr import get_asr_engine
        from utils.audio_utils import convert_to_wav
        
        audio_file_id = task['audio_file_id']
        hotwords = task['hotwords']
        
        try:
            audio_file = AudioFileModel.get_by_id(audio_file_id)
            if not audio_file:
                logger.error(f"Audio file {audio_file_id} not found")
                return
            
            wav_path = convert_to_wav(audio_file.filepath)
            
            async with self._semaphore:
                asr_engine = get_asr_engine()
                segments = await asr_engine.transcribe(wav_path, hotwords)
            
            if wav_path != audio_file.filepath and os.path.exists(wav_path):
                os.remove(wav_path)
            
            TranscriptModel.delete_by_audio_file(audio_file_id)
            
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
            TranscriptModel.create_batch(segment_dicts)
            
            AudioFileModel.update_status(audio_file_id, "completed")
            logger.info(f"Transcription completed for {audio_file_id}")
            
        except Exception as e:
            AudioFileModel.update_status(audio_file_id, "failed", str(e))
            logger.error(f"Transcription failed for {audio_file_id}: {e}")


queue = TranscribeQueue()


def get_queue() -> TranscribeQueue:
    return queue