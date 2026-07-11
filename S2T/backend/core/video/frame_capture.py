from typing import List


def generate_capture_plan(
    transcript_segments: List[dict],
    sample_interval: int = 30,
    video_duration: float = 0
) -> List[dict]:
    """生成帧捕获计划：文案关键帧 + 固定间隔帧，合并去重。

    Args:
        transcript_segments: ASR 转写段列表。
        sample_interval: 固定间隔采样（秒）。
        video_duration: 视频总时长（秒）。

    Returns:
        [{"time": float, "reason": "interval"|"keyword"}, ...]
    """
    from core.video.transcript_filter import filter_transcript

    # Track A: transcript-driven key frames
    key_moments = filter_transcript(transcript_segments)
    key_times = [m["time"] for m in key_moments]

    # Track B: fixed interval frames
    interval_times = list(range(0, int(video_duration) + 1, sample_interval))
    interval_set = set(interval_times)

    # Merge and deduplicate (within 15s window)
    all_times = sorted(set(key_times + interval_times))
    deduped: List[float] = []
    for t in all_times:
        if not deduped or t - deduped[-1] >= 15:
            deduped.append(t)

    plan = []
    for t in deduped:
        reason = "interval" if t in interval_set else "keyword"
        plan.append({"time": t, "reason": reason})

    return plan
