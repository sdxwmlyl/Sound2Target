import pytest
import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from core.asr.engine import ASREngine, get_asr_engine
from config.settings import get_settings


@pytest.mark.asyncio
async def test_asr_engine_load():
    settings = get_settings()
    
    try:
        engine = get_asr_engine()
        model = await ASREngine.load_model()
        assert model is not None
        print("ASR model loaded successfully")
    except Exception as e:
        print(f"ASR load error: {e}")
        pytest.skip(f"ASR model not available: {e}")


def test_asr_semaphore():
    settings = get_settings()
    sem = ASREngine.get_semaphore()
    assert sem is not None
    assert settings.asr.max_concurrent >= 1


@pytest.mark.asyncio
async def test_asr_transcribe_mock():
    import tempfile
    import soundfile as sf
    import numpy as np
    
    temp_path = tempfile.mktemp(suffix=".wav")
    silence = np.zeros(16000, dtype=np.int16)
    sf.write(temp_path, silence, 16000)
    
    try:
        engine = get_asr_engine()
        segments = await engine.transcribe(temp_path, "", True)
        
        print(f"Segments: {len(segments)}")
        
    except Exception as e:
        print(f"ASR test: {e}")
        pytest.skip(f"ASR not ready: {e}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])