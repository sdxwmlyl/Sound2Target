# 兼容旧配置：provider=ollama 时自动使用 llamacpp
from .llamacpp import LlamaCppLLM as OllamaLLM

__all__ = ['OllamaLLM']
