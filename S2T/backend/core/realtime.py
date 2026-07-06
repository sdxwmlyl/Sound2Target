import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional
from fastapi import WebSocket, WebSocketDisconnect

from models.audio_file import AudioFileModel
from models.transcript import TranscriptModel
from core.audio import MicrophoneCapture, SystemSoundCapture
from core.asr import get_asr_engine
from config.settings import get_settings

logger = logging.getLogger(__name__)


class RealtimeSession:
    def __init__(self, session_id: str, project_id: int, websocket: WebSocket):
        self.session_id = session_id
        self.project_id = project_id
        self.websocket = websocket
        self.audio_buffer = bytearray()
        self.is_recording = False
        self.source_type = "microphone"
        self.hotwords = ""
        self.audio_file_id: Optional[int] = None
        self.audio_filepath: Optional[str] = None
        self.wav_file = None
        self.started_at: Optional[datetime] = None
        self.capture = None
    
    async def send_message(self, msg_type: str, data: dict = None):
        try:
            message = {"type": msg_type, "timestamp": datetime.now().isoformat()}
            if data:
                message.update(data)
            await self.websocket.send_json(message)
        except Exception as e:
            # WebSocket连接已关闭，静默处理
            logger.debug(f"WebSocket closed: {e}")
            self.is_recording = False
    
    def add_audio_data(self, audio_base64: str):
        import base64
        audio_bytes = base64.b64decode(audio_base64)
        self.audio_buffer.extend(audio_bytes)
    
    def get_buffer_duration(self) -> float:
        sample_rate = 16000
        bytes_per_second = sample_rate * 2
        return len(self.audio_buffer) / bytes_per_second
    
    def clear_buffer(self):
        self.audio_buffer.clear()


class RealtimeManager:
    _sessions: Dict[str, RealtimeSession] = {}
    _transcribe_interval: float = 3.0  # 3秒转写一次，提高实时性
    
    @classmethod
    def create_session(cls, session_id: str, project_id: int, websocket: WebSocket) -> RealtimeSession:
        session = RealtimeSession(session_id, project_id, websocket)
        cls._sessions[session_id] = session
        return session
    
    @classmethod
    def get_session(cls, session_id: str) -> Optional[RealtimeSession]:
        return cls._sessions.get(session_id)
    
    @classmethod
    def remove_session(cls, session_id: str):
        session = cls._sessions.get(session_id)
        if session:
            # 停止录音设备
            if session.capture:
                session.capture.stop()
            # 关闭WAV文件
            if hasattr(session, 'wav_file') and session.wav_file:
                session.wav_file.close()
                session.wav_file = None
            # 如果有音频文件且状态是processing，更新为completed
            if session.audio_file_id and session.is_recording:
                try:
                    import asyncio
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.ensure_future(
                            asyncio.to_thread(AudioFileModel.update_status, session.audio_file_id, "completed")
                        )
                    else:
                        AudioFileModel.update_status(session.audio_file_id, "completed")
                except Exception as e:
                    logger.error(f"Error updating status on disconnect: {e}")
            session.is_recording = False
        if session_id in cls._sessions:
            del cls._sessions[session_id]
    
    @classmethod
    async def start_recording(cls, session_id: str, source_type: str, hotwords: str, audio_name: str):
        session = cls.get_session(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return
        
        settings = get_settings()
        logger.info(f"Starting recording: session={session_id}, type={source_type}, name={audio_name}")
        
        try:
            if source_type == "microphone":
                session.capture = MicrophoneCapture(
                    sample_rate=settings.audio.sample_rate,
                    chunk_duration=settings.audio.chunk_duration
                )
                session.capture.start_microphone()
                logger.info(f"Microphone capture started for session {session_id}")
            elif source_type == "system":
                session.capture = SystemSoundCapture(
                    sample_rate=settings.audio.sample_rate,
                    chunk_duration=settings.audio.chunk_duration
                )
                session.capture.start_system_sound()
                logger.info(f"System sound capture started for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to start capture: {e}")
            await session.send_message("error", {"message": f"Failed to start capture: {e}"})
            return
        
        # 创建文件路径
        import uuid
        from pathlib import Path
        upload_dir = Path(settings.storage.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        filename = f"realtime_{uuid.uuid4().hex}.wav"
        filepath = str(upload_dir / filename)
        
        audio_file = AudioFileModel.create(
            project_id=session.project_id,
            audio_name=audio_name,
            filename=filename,
            filepath=filepath,
            source_type=source_type
        )
        
        session.audio_file_id = audio_file.id
        session.audio_filepath = filepath
        session.is_recording = True
        session.source_type = source_type
        session.hotwords = hotwords
        session.started_at = datetime.now()
        session.clear_buffer()
        
        # 初始化WAV文件
        import wave
        session.wav_file = wave.open(filepath, 'wb')
        session.wav_file.setnchannels(1)
        session.wav_file.setsampwidth(2)  # 16-bit
        session.wav_file.setframerate(settings.audio.sample_rate)
        
        AudioFileModel.update_status(audio_file.id, "processing")
        
        # 只启动录音任务，不启动实时转写
        asyncio.create_task(cls._save_audio_chunks(session_id))
        
        await session.send_message("recording_started", {
            "audio_file_id": audio_file.id,
            "source_type": source_type
        })
    
    @classmethod
    async def _send_audio_chunks(cls, session_id: str):
        session = cls.get_session(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return
        
        if not session.capture:
            logger.error(f"No capture device for session {session_id}")
            return
        
        import base64
        chunk_count = 0
        empty_count = 0
        
        logger.info(f"Starting audio chunks for session {session_id}, capture={session.capture}")
        
        try:
            while session.is_recording and session.capture:
                try:
                    audio_base64 = session.capture.get_audio_base64(timeout=0.5)
                    if audio_base64:
                        empty_count = 0
                        audio_bytes = base64.b64decode(audio_base64)
                        session.audio_buffer.extend(audio_bytes)
                        
                        # 写入WAV文件
                        if hasattr(session, 'wav_file') and session.wav_file:
                            session.wav_file.writeframes(audio_bytes)
                            chunk_count += 1
                            if chunk_count % 10 == 0:
                                logger.info(f"Written {chunk_count} chunks, buffer size: {len(session.audio_buffer)}")
                        
                        await session.send_message("audio_received", {
                            "buffer_size": len(session.audio_buffer),
                            "buffer_duration": session.get_buffer_duration()
                        })
                    else:
                        empty_count += 1
                        if empty_count % 20 == 0:
                            logger.warning(f"No audio data for {empty_count} consecutive attempts")
                except Exception as e:
                    logger.error(f"Audio chunk error: {e}")
                    break
                
                await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Audio chunks loop error: {e}")
        
        logger.info(f"Audio chunks stopped for session {session_id}, total chunks: {chunk_count}")
    
    @classmethod
    async def _save_audio_chunks(cls, session_id: str):
        """只保存音频数据到文件，不进行实时转写"""
        session = cls.get_session(session_id)
        if not session or not session.capture:
            logger.error(f"Cannot start audio save: session={session}")
            return
        
        import base64
        chunk_count = 0
        
        logger.info(f"Starting audio save for session {session_id}")
        
        try:
            while session.is_recording and session.capture:
                try:
                    audio_base64 = session.capture.get_audio_base64(timeout=0.5)
                    if audio_base64:
                        audio_bytes = base64.b64decode(audio_base64)
                        session.audio_buffer.extend(audio_bytes)
                        
                        # 写入WAV文件
                        if hasattr(session, 'wav_file') and session.wav_file:
                            session.wav_file.writeframes(audio_bytes)
                            chunk_count += 1
                            if chunk_count % 20 == 0:
                                logger.info(f"Saved {chunk_count} chunks")
                except Exception as e:
                    logger.error(f"Audio save error: {e}")
                    break
                
                await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Audio save loop error: {e}")
        
        logger.info(f"Audio save stopped for session {session_id}, total chunks: {chunk_count}")
    
    @classmethod
    async def _process_realtime(cls, session_id: str):
        session = cls.get_session(session_id)
        if not session:
            return
        
        settings = get_settings()
        
        try:
            while session.is_recording:
                try:
                    # 只要buffer有数据就转写
                    if len(session.audio_buffer) > 0:
                        # 取当前buffer中的数据进行转写
                        audio_data = bytes(session.audio_buffer)
                        session.audio_buffer.clear()
                        
                        asr_engine = get_asr_engine()
                        segments = await asr_engine.transcribe_audio_data(
                            audio_data,
                            sample_rate=settings.audio.sample_rate,
                            hotwords=session.hotwords
                        )
                        
                        if segments and session.audio_file_id:
                            segment_dicts = [
                                {
                                    'audio_file_id': session.audio_file_id,
                                    'speaker_id': seg['speaker_id'],
                                    'start_time': seg['start_time'],
                                    'end_time': seg['end_time'],
                                    'text': seg['text']
                                }
                                for seg in segments
                            ]
                            await asyncio.to_thread(TranscriptModel.create_batch, segment_dicts)
                        
                        await session.send_message("realtime_result", {
                            "segments": segments,
                            "audio_file_id": session.audio_file_id
                        })
                    
                    await asyncio.sleep(cls._transcribe_interval)
                    
                except Exception as e:
                    logger.error(f"Realtime processing error: {e}")
                    if session.is_recording:
                        await session.send_message("error", {"message": str(e)})
                    break
        except Exception as e:
            logger.error(f"Realtime processing loop error: {e}")
    
    @classmethod
    async def stop_recording(cls, session_id: str):
        session = cls.get_session(session_id)
        if not session:
            return
        
        session.is_recording = False
        
        if session.capture:
            session.capture.stop()
            session.capture = None
        
        # 关闭WAV文件
        if hasattr(session, 'wav_file') and session.wav_file:
            session.wav_file.close()
            session.wav_file = None
            
            # 获取音频时长并更新
            if session.audio_filepath:
                try:
                    from utils.audio_utils import get_audio_duration
                    duration = await asyncio.to_thread(get_audio_duration, session.audio_filepath)
                    await asyncio.to_thread(
                        AudioFileModel.update_duration, 
                        session.audio_file_id, 
                        duration
                    )
                    logger.info(f"Audio duration: {duration}s")
                except Exception as e:
                    logger.error(f"Error getting duration: {e}")
        
        # 立即通知前端录音已停止
        await session.send_message("recording_stopped", {
            "audio_file_id": session.audio_file_id,
            "message": "录音已停止，正在后台转写..."
        })
        
        # 在后台执行转写，不阻塞前端
        if session.audio_filepath and session.audio_file_id:
            asyncio.create_task(cls._transcribe_in_background(
                session.audio_file_id,
                session.audio_filepath,
                session.hotwords or ""
            ))
    
    @classmethod
    async def _transcribe_in_background(cls, audio_file_id: int, audio_filepath: str, hotwords: str):
        """后台转写任务"""
        try:
            logger.info(f"Starting background transcription for {audio_filepath}")
            asr_engine = get_asr_engine()
            
            # 进度回调
            def on_progress(progress):
                logger.info(f"Transcription progress: {progress}")
            
            # 使用文件进行整体转写
            segments = await asr_engine.transcribe(
                audio_filepath, 
                hotwords=hotwords, 
                enable_diarization=True,
                progress_callback=on_progress
            )
            
            if segments:
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
                logger.info(f"Background transcription completed: {len(segments)} segments")
            
            # 更新状态为completed
            await asyncio.to_thread(AudioFileModel.update_status, audio_file_id, "completed")
            
        except Exception as e:
            logger.error(f"Background transcription error: {e}")
            await asyncio.to_thread(AudioFileModel.update_status, audio_file_id, "failed", str(e))
    
    @classmethod
    def get_active_sessions(cls) -> list:
        return [
            {
                "session_id": s.session_id,
                "project_id": s.project_id,
                "is_recording": s.is_recording,
                "source_type": s.source_type,
                "audio_file_id": s.audio_file_id,
                "buffer_duration": s.get_buffer_duration(),
                "started_at": s.started_at.isoformat() if s.started_at else None
            }
            for s in cls._sessions.values()
        ]


realtime_manager = RealtimeManager()


async def handle_realtime_websocket(websocket: WebSocket, session_id: str, project_id: int):
    await websocket.accept()
    
    session = realtime_manager.create_session(session_id, project_id, websocket)
    
    try:
        await session.send_message("connected", {
            "session_id": session_id,
            "project_id": project_id
        })
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            msg_type = message.get("type")
            
            if msg_type == "ping":
                await session.send_message("pong", {})
            
            elif msg_type == "start_recording":
                source_type = message.get("source_type", "microphone")
                hotwords = message.get("hotwords", "")
                audio_name = message.get("audio_name", f"录音_{datetime.now().strftime('%H%M%S')}")
                await realtime_manager.start_recording(session_id, source_type, hotwords, audio_name)
            
            elif msg_type == "stop_recording":
                await realtime_manager.stop_recording(session_id)
            
            elif msg_type == "set_hotwords":
                session.hotwords = message.get("hotwords", "")
                await session.send_message("hotwords_updated", {"hotwords": session.hotwords})
            
            elif msg_type == "get_status":
                await session.send_message("status", {
                    "is_recording": session.is_recording,
                    "buffer_duration": session.get_buffer_duration(),
                    "source_type": session.source_type,
                    "audio_file_id": session.audio_file_id
                })
    
    except WebSocketDisconnect:
        realtime_manager.remove_session(session_id)
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        realtime_manager.remove_session(session_id)