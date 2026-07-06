import aiohttp
from typing import Optional
from .base import BaseLLM
from config.settings import get_settings, get_llm_api_key


class AliyunLLM(BaseLLM):
    def __init__(self):
        settings = get_settings()
        self.base_url = settings.llm.aliyun.base_url
        self.model = settings.llm.aliyun.model
        self.api_key = get_llm_api_key()
    
    async def generate(self, prompt: str, **kwargs) -> str:
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, **kwargs)
    
    async def chat(self, messages: list, **kwargs) -> str:
        if not self.api_key:
            raise ValueError("Aliyun API key not configured")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4096)
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=kwargs.get("timeout", 120))
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"Aliyun error: {resp.status} - {text}")
                data = await resp.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    def get_context_size(self) -> int:
        return 8192