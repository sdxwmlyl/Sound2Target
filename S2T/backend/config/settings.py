import os
import yaml
from pathlib import Path
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ASRConfig(BaseModel):
    engine: str = "funasr"
    model: str = ""
    spk_model: str = ""
    vad_model: str = ""
    punc_model: str = ""
    max_concurrent: int = 2
    device: str = "cuda"


class OllamaConfig(BaseModel):
    base_url: str = "http://localhost:8080/v1"
    model: str = "qwen2.5-7b.gguf"
    api_key: str = ""


class AliyunConfig(BaseModel):
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model: str = "qwen-plus"
    api_key: str = ""


class DeepseekConfig(BaseModel):
    base_url: str = "https://api.deepseek.com/v1"
    model: str = "deepseek-chat"
    api_key: str = ""


class LLMConfig(BaseModel):
    provider: str = "ollama"
    ollama: OllamaConfig = OllamaConfig()
    aliyun: AliyunConfig = AliyunConfig()
    deepseek: DeepseekConfig = DeepseekConfig()


class AudioConfig(BaseModel):
    sample_rate: int = 16000
    chunk_duration: float = 0.5
    supported_formats: List[str] = ["wav", "mp3", "m4a", "flac", "ogg"]


class DatabaseConfig(BaseModel):
    path: str = "./data/s2t.db"


class StorageConfig(BaseModel):
    upload_dir: str = "./data/uploads"


class Settings(BaseModel):
    asr: ASRConfig = ASRConfig()
    llm: LLMConfig = LLMConfig()
    audio: AudioConfig = AudioConfig()
    database: DatabaseConfig = DatabaseConfig()
    storage: StorageConfig = StorageConfig()

    class Config:
        extra = "ignore"


_config: Optional[Settings] = None
_config_path: Optional[Path] = None


def get_config_path() -> Path:
    global _config_path
    if _config_path is None:
        env_path = os.getenv("S2T_CONFIG")
        if env_path:
            _config_path = Path(env_path)
        else:
            _config_path = Path(__file__).parent / "config.yaml"
    return _config_path


def load_config() -> Settings:
    global _config
    if _config is not None:
        return _config
    
    config_path = get_config_path()
    config_data: Dict[str, Any] = {}
    
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}
    
    _config = Settings(**config_data)
    return _config


def get_settings() -> Settings:
    return load_config()


def reload_config():
    global _config
    _config = None
    return load_config()


def get_llm_api_key() -> str:
    settings = get_settings()
    provider = settings.llm.provider
    
    if provider == "ollama":
        return ""
    elif provider == "aliyun":
        return os.getenv("ALIYUN_API_KEY", settings.llm.aliyun.api_key)
    elif provider == "deepseek":
        return os.getenv("DEEPSEEK_API_KEY", settings.llm.deepseek.api_key)
    return ""