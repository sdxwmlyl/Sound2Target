import os
import torch
import asyncio
import logging
from typing import List, Dict, Optional
from config.settings import get_settings
from core.model_state import get_model_state

logger = logging.getLogger(__name__)

# 抑制特定的警告日志
logging.getLogger('root').setLevel(logging.ERROR)


class ASREngine:
    _instance = None
    _model = None
    _lock = asyncio.Lock()
    _semaphore: Optional[asyncio.Semaphore] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_semaphore(cls) -> asyncio.Semaphore:
        if cls._semaphore is None:
            settings = get_settings()
            cls._semaphore = asyncio.Semaphore(settings.asr.max_concurrent)
        return cls._semaphore
    
    @classmethod
    async def load_model(cls):
        async with cls._lock:
            if cls._model is not None:
                return cls._model
            
            from funasr import AutoModel
            settings = get_settings()
            
            logger.info(f"Loading ASR models from local path...")
            # 关键修复1: speech_noise_threshold 降低VAD灵敏度，防止低音量语音被误判为静音
            # 默认值0.8太高，对远场/低音量语音不友好。0.5是会议场景推荐值
            cls._model = AutoModel(
                model=settings.asr.model,
                spk_model=settings.asr.spk_model,
                vad_model=settings.asr.vad_model,
                vad_kwargs={
                    "max_single_segment_time": 30000,
                    "speech_noise_threshold": 0.5,  # 关键！默认0.8太高，低音量语音被跳过
                },
                punc_model=settings.asr.punc_model,
                device=settings.asr.device,
                trust_remote_code=True
            )
            logger.info("ASR models loaded successfully")
            return cls._model
    
    @classmethod
    async def transcribe(
        cls,
        audio_path: str,
        hotwords: str = "",
        enable_diarization: bool = True,
        progress_callback=None
    ) -> List[Dict]:
        model_state = get_model_state()
        
        if model_state.is_llm_running:
            raise RuntimeError("LLM模型正在运行中，请等待生成完成后再试")
        
        if not await model_state.acquire_asr():
            raise RuntimeError("ASR模型正在运行中，请等待转写完成后再试")
        
        try:
            sem = cls.get_semaphore()
            async with sem:
                model = await cls.load_model()
                
                loop = asyncio.get_event_loop()
                try:
                    result = await loop.run_in_executor(
                        None,
                        cls._run_transcribe,
                        model,
                        audio_path,
                        hotwords,
                        enable_diarization,
                        progress_callback
                    )
                    return result
                except Exception:
                    model_state.force_release_asr()
                    raise
        finally:
            model_state.release_asr()
    
    @staticmethod
    def _run_transcribe(
        model,
        audio_path: str,
        hotwords: str,
        enable_diarization: bool,
        progress_callback=None
    ) -> List[Dict]:
        try:
            import soundfile as sf
            
            processed_hotwords = ""
            if hotwords:
                processed_hotwords = hotwords.replace(",", " ").replace("，", " ").strip()
            
            def on_progress(data):
                if progress_callback and 'progress' in data:
                    progress_callback(data['progress'])
            
            # 获取音频时长
            info = sf.info(audio_path)
            duration_s = info.duration
            
            # 分块处理，每块10分钟，重置VAD状态
            # 关键修复2: 阈值：短音频不切（<1分钟），中音频5分钟一块，长音频10分钟一块
            if duration_s <= 60:
                chunk_duration_s = duration_s  # 1分钟内不切块
            elif duration_s <= 600:
                chunk_duration_s = 300  # 10分钟内5分钟一块
            else:
                chunk_duration_s = 600  # 10分钟以上10分钟一块
            
            logger.info(f"Audio duration: {duration_s:.0f}s, using chunked processing (chunk={chunk_duration_s}s)")
            return ASREngine._transcribe_chunked(
                model, audio_path, processed_hotwords, 
                enable_diarization, duration_s, on_progress,
                chunk_duration=chunk_duration_s
            )
        except Exception as e:
            logger.error(f"ASR Error: {e}")
            raise
    
    @staticmethod
    def _transcribe_chunked(
        model, audio_path, hotwords, enable_diarization, 
        total_duration, on_progress, chunk_duration=600
    ) -> List[Dict]:
        """分块处理，每块独立临时文件→独立推理，彻底隔离VAD状态"""
        import soundfile as sf
        import numpy as np
        import tempfile, os
        
        # 读取整个音频
        audio, sr = sf.read(audio_path)
        chunk_samples = chunk_duration * sr
        
        all_segments = []
        offset_time = 0.0
        temp_files = []
        
        total_chunks = int(np.ceil(len(audio) / chunk_samples))
        logger.info(f"Total chunks: {total_chunks}, chunk_duration={chunk_duration}s")
        
        try:
            for i in range(total_chunks):
                start_sample = i * chunk_samples
                end_sample = min((i + 1) * chunk_samples, len(audio))
                chunk = audio[start_sample:end_sample]
                
                # 关键修复3: 每块写入独立临时文件，彻底隔离VAD内部状态
                # VAD 在 chunk 间会保持内部时间计数器（8000ms buffer），
                # 即使 cache={} 也无法完全重置，导致时间戳漂移
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                    sf.write(tmp.name, chunk, sr)
                    temp_files.append(tmp.name)
                
                logger.info(f"Processing chunk {i+1}/{total_chunks} ({offset_time:.0f}s - {min(offset_time + chunk_duration, total_duration):.0f}s)")
                
                generate_kwargs = {
                    'input': temp_files[-1],  # 用文件路径而非 numpy 数组
                    'language': 'zn',
                    'use_itn': True,
                    'batch_size_s': int(max(chunk_duration * 0.3, 30)),
                    'batch_size_threshold_s': 30,
                    'hotword': hotwords if hotwords else None,
                    'merge_vad': True,
                    'merge_length_s': 15,
                }
                if enable_diarization:
                    generate_kwargs['return_spk_res'] = True
                
                try:
                    res = model.generate(**generate_kwargs)
                except Exception as e:
                    logger.error(f"Chunk {i+1} generate() failed: {e}")
                    raise
                
                # 解析结果 — 临时文件确保 VAD 时间戳从0开始，所以必须加 offset
                chunk_segments = ASREngine._parse_segments(res)
                
                for seg in chunk_segments:
                    seg['start_time'] += offset_time
                    seg['end_time'] += offset_time
                
                all_segments.extend(chunk_segments)
                
                if on_progress:
                    progress = (i + 1) / total_chunks * 100
                    on_progress({'progress': progress})
                
                logger.info(f"Chunk {i+1} completed: {len(chunk_segments)} segments")
                
                offset_time += chunk_duration
        finally:
            # 清理临时文件
            for tf in temp_files:
                try:
                    os.unlink(tf)
                except OSError:
                    pass
        
        logger.info(f"Total segments: {len(all_segments)}")
        return all_segments
    
    @staticmethod
    def _parse_segments(res) -> List[Dict]:
        """解析FunASR返回结果"""
        segments = []
        for segment in res:
            items = segment.get('sentence_info', [segment])
            for item in items:
                speaker = item.get('spk', '0')
                timestamp = item.get('timestamp', [[0, 0]])
                start_ms = timestamp[0][0] if timestamp else 0
                end_ms = timestamp[-1][1] if timestamp else 0
                text = item.get('text', '')
                
                if text.strip():
                    segments.append({
                        'speaker_id': str(speaker),
                        'start_time': start_ms / 1000.0,
                        'end_time': end_ms / 1000.0,
                        'text': text.strip()
                    })
        return segments
    
    @classmethod
    async def transcribe_audio_data(
        cls,
        audio_data: bytes,
        sample_rate: int = 16000,
        hotwords: str = ""
    ) -> List[Dict]:
        import tempfile
        import numpy as np
        import soundfile as sf
        
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            sf.write(f.name, audio_array, sample_rate)
            temp_path = f.name
        
        try:
            result = await cls.transcribe(temp_path, hotwords)
            return result
        finally:
            import os
            if os.path.exists(temp_path):
                os.remove(temp_path)


def get_asr_engine() -> ASREngine:
    return ASREngine()