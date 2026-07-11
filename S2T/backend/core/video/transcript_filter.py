import re
from typing import List, Dict

TIER1_PATTERNS = [
    r'\d+\.?\d*\s*(GB/s|MB/s|tokens?/s|t/s|TPS|fps|ms|毫秒)',
    r'\d+\.?\d*\s*(GB|MB|TB)\b',
    r'从\s*\d+', r'达到\s*\d+', r'降到\s*\d+', r'速度\s*\d+',
]

TIER2_KEYWORDS = ["图表", "测试图", "柱状", "折线", "画面", "数据", "表格"]
TIER3_KEYWORDS = ["总结", "结论", "建议", "推荐", "一句话", "所以"]
TIER4_KEYWORDS = ["领先", "超过", "不如", "持平", "优势", "劣势", "赢", "输"]


def filter_transcript(segments: List[Dict], merge_window: float = 8.0) -> List[Dict]:
    """从转写段中筛选关键帧时间点。

    Returns:
        聚类后的关键帧列表，每个元素包含 time/tier/reason/texts 字段。
    """
    results = []
    for seg in segments:
        text = seg.get("text", "")
        start = seg.get("start_time", 0)
        tier = 0
        reason = ""

        for pat in TIER1_PATTERNS:
            if re.search(pat, text):
                tier, reason = 1, "数据点"
                break

        if tier == 0:
            for kw in TIER2_KEYWORDS:
                if kw in text:
                    tier, reason = 2, f"图表提及({kw})"
                    break

        if tier == 0:
            for kw in TIER3_KEYWORDS:
                if kw in text:
                    tier, reason = 3, f"结论({kw})"
                    break

        if tier == 0:
            for kw in TIER4_KEYWORDS:
                if kw in text:
                    tier, reason = 4, f"对比({kw})"
                    break

        if tier > 0:
            results.append({"time": start, "tier": tier, "reason": reason, "text": text})

    # Merge nearby items within merge_window
    clusters: List[Dict] = []
    for r in results:
        if clusters and r["time"] - clusters[-1]["time"] < merge_window:
            # Keep the highest-priority (lowest tier number) reason
            if r["tier"] < clusters[-1]["tier"]:
                clusters[-1]["tier"] = r["tier"]
                clusters[-1]["reason"] = r["reason"]
            clusters[-1]["texts"].append(r["text"])
        else:
            clusters.append({
                "time": r["time"],
                "tier": r["tier"],
                "reason": r["reason"],
                "texts": [r["text"]]
            })

    return clusters
