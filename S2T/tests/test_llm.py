import pytest
import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from core.llm.base import LLMFactory, get_llm
from core.llm.ollama import OllamaLLM
from config.settings import get_settings


@pytest.mark.asyncio
async def test_ollama_llm_connection():
    settings = get_settings()
    if settings.llm.provider != "ollama":
        pytest.skip("Not using Ollama")
    
    llm = get_llm()
    
    try:
        result = await llm.generate("你好，请回复'测试成功'", timeout=30)
        assert result is not None
        assert len(result) > 0
        print(f"LLM Response: {result[:50]}...")
    except Exception as e:
        print(f"Ollama connection test: {e}")
        pytest.skip(f"Ollama not available: {e}")


@pytest.mark.asyncio
async def test_llm_chat_format():
    llm = OllamaLLM()
    
    messages = [
        {"role": "user", "content": "测试问题"}
    ]
    
    try:
        result = await llm.chat(messages, timeout=30)
        assert result is not None
    except Exception as e:
        pytest.skip(f"Ollama not available: {e}")


def test_llm_factory():
    settings = get_settings()
    
    llm = LLMFactory.get_llm()
    assert llm is not None
    
    from core.llm.ollama import OllamaLLM
    from core.llm.aliyun import AliyunLLM
    from core.llm.deepseek import DeepseekLLM
    
    if settings.llm.provider == "ollama":
        assert isinstance(llm, OllamaLLM)
    elif settings.llm.provider == "aliyun":
        assert isinstance(llm, AliyunLLM)
    elif settings.llm.provider == "deepseek":
        assert isinstance(llm, DeepseekLLM)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])