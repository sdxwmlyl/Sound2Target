import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ModelState:
    """模型运行状态管理"""
    _instance = None
    _asr_running = False
    _llm_running = False
    _asr_lock = asyncio.Lock()
    _llm_lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def is_asr_running(self) -> bool:
        return self._asr_running
    
    @property
    def is_llm_running(self) -> bool:
        return self._llm_running
    
    @property
    def is_any_running(self) -> bool:
        return self._asr_running or self._llm_running
    
    async def acquire_asr(self) -> bool:
        """获取ASR运行权限，可等待LLM释放"""
        async with self._asr_lock:
            if self._llm_running:
                return False
            if self._asr_running:
                return False  # 禁止并发
            self._asr_running = True
            return True
    
    def release_asr(self):
        """释放ASR运行权限"""
        self._asr_running = False
    
    def force_release_asr(self):
        """强制释放ASR（出错时兜底）"""
        self._asr_running = False
    
    async def acquire_llm(self) -> bool:
        """获取LLM运行权限"""
        async with self._llm_lock:
            if self._asr_running:
                return False
            self._llm_running = True
            return True
    
    def release_llm(self):
        """释放LLM运行权限"""
        self._llm_running = False
    
    def get_status_message(self) -> Optional[str]:
        """获取当前状态提示信息"""
        if self._asr_running:
            return "ASR模型正在运行中，请等待转写完成后再试"
        if self._llm_running:
            return "LLM模型正在运行中，请等待生成完成后再试"
        return None


model_state = ModelState()


def get_model_state() -> ModelState:
    return model_state