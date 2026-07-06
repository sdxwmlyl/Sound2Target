"""
观点演变提取 API
基于 large-file-reader skill 的观点追踪机制，使用本地 LLM 对会议转录
进行深度分析：观点演变、逻辑链、矛盾检测、前提条件、待确认事项。

核心区别于 summarize：
- summarize = 逐块摘要再汇总（压缩信息）
- viewpoint = 逐块提取观点版本链 + 跨块合并演变（追踪变化）
"""

import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict

from core.llm import get_llm
from models.transcript import TranscriptModel
from models.audio_file import AudioFileModel
from models.project import ProjectModel

router = APIRouter(prefix="/api/viewpoint", tags=["viewpoint"])


# ============================================================
# 请求/响应模型
# ============================================================

class ViewpointExtractRequest(BaseModel):
    project_id: int
    custom_topics: Optional[Dict[str, list]] = None  # 自定义主题 → 关键词映射


# ============================================================
# Prompt 模板
# ============================================================

TOPICS_EXTRACTION_PROMPT = """你是一位专业的会议分析师。请从以下会议转录片段中识别所有讨论主题。

对于每个主题，提取：
1. 主题名称
2. 涉及的关键观点（原文引用）
3. 发言人
4. 时间戳
5. 观点是否为最终确认版本（标记"最终"或"初始"/"待定"）

特别注意观点修正信号：
- 直接修正："不对"、"错了"、"改一下"
- 转折修正："但是"、"不过"、"实际上"、"其实"
- 最终确认："最终"、"确认"、"定下来"、"就这样"
- 否定前文："不用"、"不需要"、"取消"

请以 JSON 格式返回：
```json
{{
  "topics": [
    {{
      "name": "主题名称",
      "opinions": [
        {{
          "content": "观点内容",
          "speaker": "发言人",
          "timestamp": "时间戳",
          "status": "最终/初始/待定",
          "is_modification": false,
          "modifies_what": ""
        }}
      ]
    }}
  ],
  "decisions": ["已确认的决策"],
  "open_questions": ["未确认的问题"]
}}
```

转录内容：
{transcript}"""


MERGE_PROMPT = """你是一位专业的会议分析师。以下是从多个会议片段中提取的初步观点数据。

请合并和精炼这些数据，完成以下任务：

1. **观点演变追踪**：同一主题如果在不同片段中有不同表述，建立版本链
   - 记录从 v1 → v2 → v3 的演变过程
   - 标记每次变化的原因

2. **逻辑链构建**：识别观点之间的因果/推导关系
   - "因为A所以B" 的因果链
   - "如果A则B" 的条件链
   - "A支撑B" 的论据链

3. **矛盾检测**：找出前后不一致的表述
   - 标记已解决的矛盾（有后续版本修正）
   - 标记未解决的矛盾（无明确结论）

4. **前提条件**：记录每个结论的适用条件和边界

5. **待确认事项**：标记需要后续跟进的问题

请以 JSON 格式返回：
```json
{{
  "final_decisions": [
    {{
      "topic": "主题",
      "decision": "最终结论",
      "reasoning": "决策依据",
      "premise": "前提条件（可选）",
      "invalidation": "失效条件（可选）"
    }}
  ],
  "opinion_evolution": [
    {{
      "topic": "主题",
      "versions": [
        {{"version": 1, "content": "观点", "timestamp": "时间", "speaker": "发言人", "status": "已修正", "reason": "修正原因"}},
        {{"version": 2, "content": "观点", "timestamp": "时间", "speaker": "发言人", "status": "最终", "reason": ""}}
      ]
    }}
  ],
  "logic_chains": [
    {{
      "conclusion": "结论",
      "steps": ["前提1", "推导2", "结论3"],
      "dependencies": ["依赖的观点"]
    }}
  ],
  "contradictions": {{
    "resolved": [
      {{"topic": "主题", "early": "早期观点", "final": "最终观点", "resolution": "如何解决"}}
    ],
    "unresolved": [
      {{"topic": "主题", "side_a": "观点A", "side_b": "观点B"}}
    ]
  }},
  "open_questions": [
    {{
      "question": "待确认问题",
      "context": "相关上下文",
      "who_needs_to_confirm": "需要谁确认"
    }}
  ]
}}
```

初步观点数据：
{preliminary_data}"""

REPORT_FORMAT_PROMPT = """请将以下结构化观点分析数据，转换为一份清晰的 Markdown 报告。

报告结构：
# 会议观点分析报告

## 一、最终决策
每个主题的最终结论，附决策依据和前提条件。

## 二、观点演变
重要观点的变化过程，用表格展示版本链。

## 三、逻辑推导
关键结论的推导路径，用箭头链展示。

## 四、矛盾与分歧
已解决和未解决的矛盾。

## 五、待确认事项
需要后续跟进的问题，标注需要谁确认。

## 六、前提条件汇总
各结论的适用边界和失效条件。

要求：
- 只基于提供的数据，不编造内容
- 观点演变必须展示变化过程，不只写最终版
- 语言简洁专业

数据：
{analysis_data}"""


# ============================================================
# 工具函数
# ============================================================

def _format_transcript_for_viewpoint(segments) -> str:
    """格式化转录段落为带时间戳和发言人的文本"""
    lines = []
    for s in segments:
        start_min = int(s.start_time // 60)
        start_sec = int(s.start_time % 60)
        end_min = int(s.end_time // 60)
        end_sec = int(s.end_time % 60)
        ts = f"{start_min:02d}:{start_sec:02d}-{end_min:02d}:{end_sec:02d}"
        speaker = f"发言人{s.speaker_id}" if hasattr(s, 'speaker_id') and s.speaker_id is not None else "发言人0"
        lines.append(f"[{ts}] {speaker}: {s.text}")
    return "\n".join(lines)


def _split_into_chunks(text: str, max_chars: int = 3000) -> list:
    """按行边界切分文本为多个块"""
    lines = text.split("\n")
    chunks = []
    current = []
    current_len = 0

    for line in lines:
        if current_len + len(line) > max_chars and current:
            chunks.append("\n".join(current))
            current = [line]
            current_len = len(line)
        else:
            current.append(line)
            current_len += len(line)

    if current:
        chunks.append("\n".join(current))

    return chunks


def _extract_json_from_response(text: str) -> dict:
    """从 LLM 响应中提取 JSON（兼容 markdown code block）"""
    # 尝试直接解析
    text = text.strip()
    if text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    # 尝试提取 ```json ... ``` 块
    import re
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 尝试找第一个 { 到最后一个 }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(text[first_brace:last_brace + 1])
        except json.JSONDecodeError:
            pass

    return {"raw_text": text}


# ============================================================
# 核心处理流程
# ============================================================

async def _phase1_extract_from_chunks(llm, chunks: list, custom_topics: dict = None) -> list:
    """Phase 1: 逐块提取观点"""
    all_extractions = []

    for i, chunk in enumerate(chunks):
        prompt = TOPICS_EXTRACTION_PROMPT.format(transcript=chunk)

        if custom_topics:
            topics_hint = "、".join(custom_topics.keys())
            prompt = f"特别关注以下主题：{topics_hint}\n\n{prompt}"

        try:
            response = await llm.generate(prompt, max_tokens=2000, timeout=300)
            extracted = _extract_json_from_response(extracted_response := response)
            extracted["_chunk_index"] = i
            all_extractions.append(extracted)
        except Exception as e:
            all_extractions.append({
                "_chunk_index": i,
                "error": str(e),
                "topics": [],
                "decisions": [],
                "open_questions": []
            })

    return all_extractions


async def _phase2_merge_and_analyze(llm, extractions: list) -> dict:
    """Phase 2: 合并所有块的提取结果，构建演变链"""
    # 将所有提取结果压缩为文本
    data_parts = []
    for ext in extractions:
        chunk_idx = ext.get("_chunk_index", "?")
        if "error" in ext:
            data_parts.append(f"[片段{chunk_idx + 1}] 提取失败: {ext['error']}")
        else:
            data_parts.append(f"[片段{chunk_idx + 1}]\n{json.dumps(ext, ensure_ascii=False, indent=2)}")

    preliminary_data = "\n\n".join(data_parts)

    # 如果数据太长，截断
    MAX_MERGE_INPUT = 8000
    if len(preliminary_data) > MAX_MERGE_INPUT:
        preliminary_data = preliminary_data[:MAX_MERGE_INPUT] + "\n\n[... 数据过长，已截断 ...]"

    prompt = MERGE_PROMPT.format(preliminary_data=preliminary_data)

    try:
        response = await llm.generate(prompt, max_tokens=4000, timeout=600)
        return _extract_json_from_response(response)
    except Exception as e:
        return {"error": str(e), "raw_extractions": extractions}


async def _phase3_format_report(llm, analysis_data: dict) -> str:
    """Phase 3: 将结构化分析转为可读 Markdown 报告"""
    data_text = json.dumps(analysis_data, ensure_ascii=False, indent=2)

    # 如果数据太长，截断
    MAX_REPORT_INPUT = 6000
    if len(data_text) > MAX_REPORT_INPUT:
        data_text = data_text[:MAX_REPORT_INPUT] + "\n\n[... 数据过长，已截断 ...]"

    prompt = REPORT_FORMAT_PROMPT.format(analysis_data=data_text)

    try:
        response = await llm.generate(prompt, max_tokens=4000, timeout=300)
        return response
    except Exception as e:
        # 格式化失败，返回原始 JSON
        return f"# 观点分析报告（格式化失败，返回原始数据）\n\n```json\n{data_text}\n```\n\n错误: {e}"


# ============================================================
# API 端点
# ============================================================

@router.post("/extract")
async def extract_viewpoints(request: ViewpointExtractRequest):
    """
    对项目所有已完成转写进行观点演变提取。

    三阶段处理：
    1. 逐块提取主题和观点（保留时间戳和发言人）
    2. 跨块合并，构建观点演变链、逻辑链、矛盾检测
    3. 格式化为可读 Markdown 报告

    SSE 流式返回处理进度和最终结果。
    """
    project = ProjectModel.get_by_id(request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 获取所有已完成的音频文件
    completed_files = [
        af for af in project.audio_files
        if af.status == "completed"
    ]
    if not completed_files:
        raise HTTPException(status_code=400, detail="没有已完成的转写，无法提取观点")

    # 收集所有转写段落
    all_segments = []
    for af in completed_files:
        segments = TranscriptModel.get_by_audio_file(af.id)
        if segments:
            all_segments.extend(segments)

    if not all_segments:
        raise HTTPException(status_code=400, detail="转写内容为空")

    # 按时间排序
    all_segments.sort(key=lambda s: s.start_time)

    # 格式化并分块
    full_text = _format_transcript_for_viewpoint(all_segments)
    chunks = _split_into_chunks(full_text, max_chars=3000)

    try:
        llm = get_llm()

        async def generate():
            total_chunks = len(chunks)

            # ---- Phase 1: 逐块提取 ----
            yield f"data: {json.dumps({'phase': 'extracting', 'total_chunks': total_chunks, 'message': f'开始逐块提取观点（共{total_chunks}块）'})}\n\n"

            extractions = []
            for i, chunk in enumerate(chunks):
                prompt = TOPICS_EXTRACTION_PROMPT.format(transcript=chunk)

                if request.custom_topics:
                    topics_hint = "、".join(request.custom_topics.keys())
                    prompt = f"特别关注以下主题：{topics_hint}\n\n{prompt}"

                try:
                    response = await llm.generate(prompt, max_tokens=2000, timeout=300)
                    extracted = _extract_json_from_response(response)
                    extracted["_chunk_index"] = i
                    extractions.append(extracted)

                    topic_count = len(extracted.get("topics", []))
                    yield f"data: {json.dumps({'phase': 'extracting', 'chunk': i + 1, 'total': total_chunks, 'topics_found': topic_count, 'message': f'片段{i+1}/{total_chunks} 提取完成，发现{topic_count}个主题'})}\n\n"
                except Exception as e:
                    extractions.append({
                        "_chunk_index": i,
                        "error": str(e),
                        "topics": [],
                        "decisions": [],
                        "open_questions": []
                    })
                    yield f"data: {json.dumps({'phase': 'extracting', 'chunk': i + 1, 'total': total_chunks, 'error': str(e), 'message': f'片段{i+1}/{total_chunks} 提取失败: {e}'})}\n\n"

            # ---- Phase 2: 合并分析 ----
            yield f"data: {json.dumps({'phase': 'merging', 'message': '正在合并分析观点演变...'})}\n\n"

            # 压缩数据
            data_parts = []
            for ext in extractions:
                chunk_idx = ext.get("_chunk_index", "?")
                if "error" in ext:
                    data_parts.append(f"[片段{chunk_idx + 1}] 提取失败: {ext['error']}")
                else:
                    data_parts.append(f"[片段{chunk_idx + 1}]\n{json.dumps(ext, ensure_ascii=False, indent=2)}")

            preliminary_data = "\n\n".join(data_parts)
            MAX_MERGE_INPUT = 8000
            if len(preliminary_data) > MAX_MERGE_INPUT:
                preliminary_data = preliminary_data[:MAX_MERGE_INPUT] + "\n\n[... 数据过长，已截断 ...]"

            merge_prompt = MERGE_PROMPT.format(preliminary_data=preliminary_data)
            try:
                merge_response = await llm.generate(merge_prompt, max_tokens=4000, timeout=600)
                analysis = _extract_json_from_response(merge_response)
            except Exception as e:
                analysis = {"error": str(e), "raw_extractions": extractions}

            yield f"data: {json.dumps({'phase': 'merging', 'message': '观点演变分析完成'})}\n\n"

            # ---- Phase 3: 格式化报告 ----
            yield f"data: {json.dumps({'phase': 'formatting', 'message': '正在生成报告...'})}\n\n"

            data_text = json.dumps(analysis, ensure_ascii=False, indent=2)
            MAX_REPORT_INPUT = 6000
            if len(data_text) > MAX_REPORT_INPUT:
                data_text = data_text[:MAX_REPORT_INPUT] + "\n\n[... 数据过长，已截断 ...]"

            report_prompt = REPORT_FORMAT_PROMPT.format(analysis_data=data_text)
            try:
                report = await llm.generate(report_prompt, max_tokens=4000, timeout=300)
            except Exception as e:
                report = f"# 观点分析报告（格式化失败）\n\n```json\n{data_text}\n```\n\n错误: {e}"

            # ---- 返回最终结果 ----
            final_result = {
                "done": True,
                "report": report,
                "structured_data": analysis,
                "stats": {
                    "total_segments": len(all_segments),
                    "total_chunks": total_chunks,
                    "char_count": len(full_text)
                }
            }
            yield f"data: {json.dumps(final_result, ensure_ascii=False)}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-sync")
async def extract_viewpoints_sync(request: ViewpointExtractRequest):
    """
    同步版本：返回完整结果（非流式）。
    适合 MCP 工具调用（一次性返回）。
    """
    project = ProjectModel.get_by_id(request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    completed_files = [
        af for af in project.audio_files
        if af.status == "completed"
    ]
    if not completed_files:
        raise HTTPException(status_code=400, detail="没有已完成的转写，无法提取观点")

    all_segments = []
    for af in completed_files:
        segments = TranscriptModel.get_by_audio_file(af.id)
        if segments:
            all_segments.extend(segments)

    if not all_segments:
        raise HTTPException(status_code=400, detail="转写内容为空")

    all_segments.sort(key=lambda s: s.start_time)
    full_text = _format_transcript_for_viewpoint(all_segments)
    chunks = _split_into_chunks(full_text, max_chars=3000)

    try:
        llm = get_llm()

        # Phase 1
        extractions = []
        for i, chunk in enumerate(chunks):
            prompt = TOPICS_EXTRACTION_PROMPT.format(transcript=chunk)
            if request.custom_topics:
                topics_hint = "、".join(request.custom_topics.keys())
                prompt = f"特别关注以下主题：{topics_hint}\n\n{prompt}"
            try:
                response = await llm.generate(prompt, max_tokens=2000, timeout=300)
                extracted = _extract_json_from_response(response)
                extracted["_chunk_index"] = i
                extractions.append(extracted)
            except Exception as e:
                extractions.append({"_chunk_index": i, "error": str(e), "topics": []})

        # Phase 2
        data_parts = []
        for ext in extractions:
            chunk_idx = ext.get("_chunk_index", "?")
            if "error" in ext:
                data_parts.append(f"[片段{chunk_idx + 1}] 错误: {ext['error']}")
            else:
                data_parts.append(f"[片段{chunk_idx + 1}]\n{json.dumps(ext, ensure_ascii=False, indent=2)}")

        preliminary_data = "\n\n".join(data_parts)
        if len(preliminary_data) > 8000:
            preliminary_data = preliminary_data[:8000] + "\n\n[截断]"

        merge_prompt = MERGE_PROMPT.format(preliminary_data=preliminary_data)
        merge_response = await llm.generate(merge_prompt, max_tokens=4000, timeout=600)
        analysis = _extract_json_from_response(merge_response)

        # Phase 3
        data_text = json.dumps(analysis, ensure_ascii=False, indent=2)
        if len(data_text) > 6000:
            data_text = data_text[:6000] + "\n\n[截断]"

        report_prompt = REPORT_FORMAT_PROMPT.format(analysis_data=data_text)
        report = await llm.generate(report_prompt, max_tokens=4000, timeout=300)

        return {
            "success": True,
            "project_id": request.project_id,
            "project_name": project.name,
            "report": report,
            "structured_data": analysis,
            "stats": {
                "total_segments": len(all_segments),
                "total_chunks": len(chunks),
                "char_count": len(full_text)
            }
        }

    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
