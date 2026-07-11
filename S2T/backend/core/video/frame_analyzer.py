import base64
import json
import os
import urllib.request
import logging
from config.settings import get_settings

logger = logging.getLogger(__name__)


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def analyze_frame(image_path: str, timestamp: float) -> dict:
    """调用多模态大模型识别单帧内容。

    Returns:
        {"timestamp", "frame_path", "description", "content_type"}
    """
    settings = get_settings()
    mm = settings.multimodal

    api_key = mm.api_key
    if not api_key:
        api_key = os.getenv("MULTIMODAL_API_KEY", "")

    if not api_key:
        raise RuntimeError(
            "Multimodal API key not configured "
            "(settings.multimodal.api_key or MULTIMODAL_API_KEY env)"
        )

    image_b64 = encode_image(image_path)

    messages = [{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
            {"type": "text", "text": (
                "请识别这张图片中的内容。如果是图表/表格/数据，请提取所有可见的数值和标签。"
                "如果是文字/字幕，请完整提取。用中文回答，简洁准确。"
            )}
        ]
    }]

    body = {
        "model": mm.model,
        "messages": messages,
        "max_tokens": mm.max_tokens
    }

    url = f"{mm.base_url}/chat/completions"
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    })

    logger.info(f"Analyzing frame at {timestamp}s: {image_path}")
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode())

    description = result["choices"][0]["message"]["content"]

    # Simple content type classification
    content_type = "text"
    if any(kw in description for kw in ["图表", "柱状", "折线", "曲线图", "饼图"]):
        content_type = "chart"
    elif any(kw in description for kw in ["表格", "对比表", "规格表"]):
        content_type = "table"

    return {
        "timestamp": timestamp,
        "frame_path": image_path,
        "description": description,
        "content_type": content_type
    }
