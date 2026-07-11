from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, AsyncGenerator


class BaseLLM(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        pass
    
    @abstractmethod
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        pass
    
    @abstractmethod
    async def chat(self, messages: list, **kwargs) -> str:
        pass
    
    @abstractmethod
    async def chat_stream(self, messages: list, **kwargs) -> AsyncGenerator[str, None]:
        pass
    
    def get_context_size(self) -> int:
        return 4096


class LLMFactory:
    _instances: Dict[str, BaseLLM] = {}
    _last_provider: Optional[str] = None
    
    @classmethod
    def get_llm(cls) -> BaseLLM:
        from config.settings import get_settings
        settings = get_settings()
        provider = settings.llm.provider
        
        if cls._last_provider and cls._last_provider != provider:
            cls._instances.clear()
        cls._last_provider = provider
        
        if provider not in cls._instances:
            if provider == "llamacpp":
                from .llamacpp import LlamaCppLLM
                cls._instances[provider] = LlamaCppLLM()
            elif provider == "ollama":
                # 兼容旧配置，实际走同一个 OpenAI 兼容 API
                from .llamacpp import LlamaCppLLM
                cls._instances[provider] = LlamaCppLLM()
            elif provider == "aliyun":
                from .aliyun import AliyunLLM
                cls._instances[provider] = AliyunLLM()
            elif provider == "deepseek":
                from .deepseek import DeepseekLLM
                cls._instances[provider] = DeepseekLLM()
            else:
                raise ValueError(f"Unknown LLM provider: {provider}")
        
        return cls._instances[provider]
    
    @classmethod
    def reset(cls):
        cls._instances.clear()


def get_llm() -> BaseLLM:
    return LLMFactory.get_llm()