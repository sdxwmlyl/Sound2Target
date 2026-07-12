import os
import yaml
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from config.settings import get_settings, get_config_path, reload_config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["settings"])


class LLMProviderConfig(BaseModel):
    base_url: str = ""
    model: str = ""
    api_key: str = ""


class MultimodalProviderConfig(BaseModel):
    base_url: str = ""
    model: str = ""
    api_key: str = ""
    max_tokens: int = 2048


class ASRSettings(BaseModel):
    engine: Optional[str] = None
    device: Optional[str] = None
    max_concurrent: Optional[int] = None


class LLMSettings(BaseModel):
    provider: Optional[str] = None
    llamacpp: Optional[LLMProviderConfig] = None
    aliyun: Optional[LLMProviderConfig] = None
    deepseek: Optional[LLMProviderConfig] = None


class MultimodalSettings(BaseModel):
    provider: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    max_tokens: Optional[int] = None


class FullConfigUpdate(BaseModel):
    asr: Optional[ASRSettings] = None
    llm: Optional[LLMSettings] = None
    multimodal: Optional[MultimodalSettings] = None


def _read_yaml() -> Dict[str, Any]:
    path = get_config_path()
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def _write_yaml(data: Dict[str, Any]):
    path = get_config_path()
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def _mask_key(key: str) -> str:
    """Mask API key for display: show first 4 and last 4 chars."""
    if not key or len(key) <= 12:
        return "****" if key else ""
    return key[:4] + "*" * (len(key) - 8) + key[-4:]


@router.get("/settings")
async def get_full_settings():
    """Return full settings for the frontend configuration page."""
    cfg = _read_yaml()
    settings = get_settings()

    # Mask API keys for security
    llm_data = cfg.get("llm", {})
    for provider in ("llamacpp", "aliyun", "deepseek"):
        if provider in llm_data and "api_key" in llm_data[provider]:
            key = llm_data[provider]["api_key"]
            llm_data[provider]["api_key"] = _mask_key(key) if key else ""

    mm_data = cfg.get("multimodal", {})
    if "api_key" in mm_data:
        key = mm_data["api_key"]
        mm_data["api_key"] = _mask_key(key) if key else ""

    # Check model availability: local path exists OR ModelScope cache has it
    def _check_model(path_or_empty: str, default_id: str) -> bool:
        if path_or_empty:
            return Path(path_or_empty).exists()
        # Check ModelScope cache
        cache_dir = Path.home() / ".cache" / "modelscope" / "hub" / "models" / default_id.replace("/", "/")
        return cache_dir.exists()

    from core.asr.engine import ASREngine
    models = ASREngine.DEFAULT_MODELS

    return {
        "asr": {
            "engine": settings.asr.engine,
            "device": settings.asr.device,
            "max_concurrent": settings.asr.max_concurrent,
            "model_path": settings.asr.model or "auto-download",
            "has_model": _check_model(settings.asr.model, models["model"]),
            "model_status": {
                "main": _check_model(settings.asr.model, models["model"]),
                "spk": _check_model(settings.asr.spk_model, models["spk_model"]),
                "vad": _check_model(settings.asr.vad_model, models["vad_model"]),
                "punc": _check_model(settings.asr.punc_model, models["punc_model"]),
            },
        },
        "llm": {
            "provider": settings.llm.provider,
            "llamacpp": {
                "base_url": settings.llm.llamacpp.base_url,
                "model": settings.llm.llamacpp.model,
                "api_key": _mask_key(settings.llm.llamacpp.api_key) if settings.llm.llamacpp.api_key else "",
            },
            "aliyun": {
                "base_url": settings.llm.aliyun.base_url,
                "model": settings.llm.aliyun.model,
                "api_key": _mask_key(settings.llm.aliyun.api_key) if settings.llm.aliyun.api_key else "",
            },
            "deepseek": {
                "base_url": settings.llm.deepseek.base_url,
                "model": settings.llm.deepseek.model,
                "api_key": _mask_key(settings.llm.deepseek.api_key) if settings.llm.deepseek.api_key else "",
            },
        },
        "multimodal": {
            "provider": settings.multimodal.provider,
            "base_url": settings.multimodal.base_url,
            "model": settings.multimodal.model,
            "api_key": _mask_key(settings.multimodal.api_key) if settings.multimodal.api_key else "",
            "max_tokens": settings.multimodal.max_tokens,
        },
        "audio": {
            "supported_formats": settings.audio.supported_formats,
        },
    }


@router.put("/settings")
async def update_settings(update: FullConfigUpdate):
    """Update settings and persist to config.yaml."""
    cfg = _read_yaml()

    # ── ASR ──
    if update.asr:
        asr = cfg.setdefault("asr", {})
        if update.asr.engine is not None:
            asr["engine"] = update.asr.engine
        if update.asr.device is not None:
            asr["device"] = update.asr.device
        if update.asr.max_concurrent is not None:
            val = max(1, min(8, update.asr.max_concurrent))
            asr["max_concurrent"] = val

    # ── LLM ──
    if update.llm:
        llm = cfg.setdefault("llm", {})
        if update.llm.provider is not None:
            llm["provider"] = update.llm.provider
        for provider_name in ("llamacpp", "aliyun", "deepseek"):
            provider_update = getattr(update.llm, provider_name, None)
            if provider_update:
                section = llm.setdefault(provider_name, {})
                for field in ("base_url", "model", "api_key"):
                    val = getattr(provider_update, field, None)
                    # Skip masked keys (contain *)
                    if val is not None and "*" not in str(val):
                        section[field] = val

    # ── Multimodal ──
    if update.multimodal:
        mm = cfg.setdefault("multimodal", {})
        if update.multimodal.provider is not None:
            mm["provider"] = update.multimodal.provider
        if update.multimodal.base_url is not None:
            mm["base_url"] = update.multimodal.base_url
        if update.multimodal.model is not None:
            mm["model"] = update.multimodal.model
        if update.multimodal.api_key is not None and "*" not in str(update.multimodal.api_key):
            mm["api_key"] = update.multimodal.api_key
        if update.multimodal.max_tokens is not None:
            mm["max_tokens"] = max(256, min(16384, update.multimodal.max_tokens))

    _write_yaml(cfg)
    reload_config()
    logger.info("Settings updated and reloaded")

    return {"message": "Settings updated", "restart_note": "ASR 和 LLM 配置变更将在下次调用时生效"}
