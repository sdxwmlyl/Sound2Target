import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def merge_content(
    transcript_segments: List[Dict],
    frame_descriptions: List[Dict],
    window: float = 15.0
) -> List[Dict]:
    """合并转写文案和视觉帧描述，按时间对齐去重。

    Args:
        transcript_segments: ASR 转写段列表，需含 start_time / text 字段。
        frame_descriptions: 帧分析结果列表，需含 timestamp / description 字段。
        window: 合并窗口（秒），时间差小于此值的相邻条目会合并。

    Returns:
        按时间排序的融合内容列表。
    """
    items: List[Dict] = []

    for seg in transcript_segments:
        items.append({
            "time": seg.get("start_time", 0),
            "source": "transcript",
            "text": seg.get("text", ""),
            "type": "spoken"
        })

    for frame in frame_descriptions:
        items.append({
            "time": frame.get("timestamp", 0),
            "source": "visual",
            "text": frame.get("description", ""),
            "frame_path": frame.get("frame_path", ""),
            "content_type": frame.get("content_type", "unknown"),
            "type": "visual"
        })

    items.sort(key=lambda x: x["time"])

    merged: List[Dict] = []
    for item in items:
        if merged and item["time"] - merged[-1]["time"] < window:
            # Merge with previous cluster
            if item["source"] != merged[-1].get("source"):
                if item["source"] == "visual":
                    merged[-1]["visual_description"] = item.get("text", "")
                else:
                    merged[-1]["transcript_text"] = item.get("text", "")
                merged[-1]["sources"] = "both"
            else:
                # Same source — append text
                merged[-1]["text"] = merged[-1].get("text", "") + "\n" + item.get("text", "")
        else:
            merged.append(item)

    logger.info(f"Merged content: {len(transcript_segments)} transcript + "
                f"{len(frame_descriptions)} frames → {len(merged)} items")
    return merged
