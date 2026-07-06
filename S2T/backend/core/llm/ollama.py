import aiohttp
import json
from typing import Optional, AsyncGenerator
from .base import BaseLLM
from config.settings import get_settings
from core.model_state import get_model_state


class OllamaLLM(BaseLLM):
    """LLM provider via LM Studio (OpenAI-compatible API)"""
    
    def __init__(self):
        self._load_config()
    
    def _load_config(self):
        settings = get_settings()
        self.base_url = settings.llm.ollama.base_url
        self.model = settings.llm.ollama.model
        self.api_key = getattr(settings.llm.ollama, 'api_key', '')
    
    async def generate(self, prompt: str, **kwargs) -> str:
        self._load_config()
        model_state = get_model_state()
        
        if model_state.is_asr_running:
            raise RuntimeError("ASR模型正在运行中，请等待转写完成后再试")
        
        if not await model_state.acquire_llm():
            raise RuntimeError("LLM模型正在运行中，请等待生成完成后再试")
        
        try:
            # OpenAI-compatible completions API
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "max_tokens": kwargs.get("max_tokens", 4096),
                "chat_template_kwargs": {"enable_thinking": False}
            }
            
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=kwargs.get("timeout", 600))
                ) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        raise Exception(f"LM Studio error {resp.status}: {text[:200]}")
                    data = await resp.json()
                    msg = data.get("choices", [{}])[0].get("message", {})
                    response = msg.get("content", "") or msg.get("reasoning_content", "")
                    return response
        finally:
            model_state.release_llm()
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        self._load_config()
        model_state = get_model_state()
        
        if model_state.is_asr_running:
            raise RuntimeError("ASR模型正在运行中，请等待转写完成后再试")
        
        if not await model_state.acquire_llm():
            raise RuntimeError("LLM模型正在运行中，请等待生成完成后再试")
        
        try:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
                "max_tokens": kwargs.get("max_tokens", 4096),
                "chat_template_kwargs": {"enable_thinking": False}
            }
            
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=kwargs.get("timeout", 600))
                ) as resp:
                    if resp.status != 200:
                        raise Exception(f"LM Studio error: {resp.status}")
                    
                    async for line in resp.content:
                        line_text = line.decode('utf-8', errors='ignore').strip()
                        if line_text.startswith("data: ") and line_text != "data: [DONE]":
                            try:
                                data = json.loads(line_text[6:])
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                token = delta.get("content", "") or delta.get("reasoning_content", "")
                                if token:
                                    yield token
                            except json.JSONDecodeError:
                                continue
        finally:
            model_state.release_llm()
    
    async def chat(self, messages: list, **kwargs) -> str:
        self._load_config()
        model_state = get_model_state()
        
        if model_state.is_asr_running:
            raise RuntimeError("ASR模型正在运行中，请等待转写完成后再试")
        
        if not await model_state.acquire_llm():
            raise RuntimeError("LLM模型正在运行中，请等待生成完成后再试")
        
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "max_tokens": kwargs.get("max_tokens", 4096)
            }
            
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=kwargs.get("timeout", 600))
                ) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        raise Exception(f"LM Studio error {resp.status}: {text[:200]}")
                    data = await resp.json()
                    msg = data.get("choices", [{}])[0].get("message", {})
                    response = msg.get("content", "") or msg.get("reasoning_content", "")
                    return response
        finally:
            model_state.release_llm()
    
    async def chat_stream(self, messages: list, **kwargs) -> AsyncGenerator[str, None]:
        self._load_config()
        model_state = get_model_state()
        
        if model_state.is_asr_running:
            raise RuntimeError("ASR模型正在运行中，请等待转写完成后再试")
        
        if not await model_state.acquire_llm():
            raise RuntimeError("LLM模型正在运行中，请等待生成完成后再试")
        
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": True,
                "max_tokens": kwargs.get("max_tokens", 4096),
                "chat_template_kwargs": {"enable_thinking": False}
            }
            
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=kwargs.get("timeout", 600))
                ) as resp:
                    if resp.status != 200:
                        raise Exception(f"LM Studio error: {resp.status}")
                    
                    async for line in resp.content:
                        line_text = line.decode('utf-8', errors='ignore').strip()
                        if line_text.startswith("data: ") and line_text != "data: [DONE]":
                            try:
                                data = json.loads(line_text[6:])
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                token = delta.get("content", "") or delta.get("reasoning_content", "")
                                if token:
                                    yield token
                            except json.JSONDecodeError:
                                continue
        finally:
            model_state.release_llm()
    
    def get_context_size(self) -> int:
        return 16384
