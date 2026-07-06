def speaker_diarization(audio_path: str, num_speakers: int = None):
    """
    发言人分离功能 - 已集成到ASR引擎中
    FunASR AutoModel 自动执行发言人分离
    """
    from core.asr import get_asr_engine
    
    engine = get_asr_engine()
    return engine.transcribe(audio_path, enable_diarization=True)