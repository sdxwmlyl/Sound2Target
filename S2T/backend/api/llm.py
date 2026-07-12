import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Optional
from pydantic import BaseModel

from core.llm import get_llm
from models.transcript import TranscriptModel
from models.audio_file import AudioFileModel
from models.project import ProjectModel
from models.ai_chat import AIChatModel


router = APIRouter(prefix="/api/llm", tags=["llm"])


class SummarizeRequest(BaseModel):
    audio_file_id: int
    prompt: str = "- 会议主题是什么？\n- 罗列每个发言人的核心观点\n- 整理决议事项和后续待办"
    speaker_names: Optional[dict] = None  # {"0": "张总", "1": "李工"}


class ChatRequest(BaseModel):
    project_id: int
    question: str
    context: str = ""
    history: Optional[List[dict]] = None
    temperature: float = 0.4
    max_context: int = 3
    speaker_names: Optional[dict] = None


@router.post("/summarize")
async def summarize_transcript(request: SummarizeRequest):
    audio_file = AudioFileModel.get_by_id(request.audio_file_id)
    if not audio_file:
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    segments = TranscriptModel.get_by_audio_file(request.audio_file_id)
    if not segments:
        raise HTTPException(status_code=400, detail="No transcript available")
    
    transcript_text = format_transcript_for_llm(segments, request.speaker_names)
    
    # 分块总结策略：每块 ~2500 字符保留 prompt 空间
    MAX_CHUNK = 2500
    
    if len(transcript_text) > MAX_CHUNK:
        # 按行均分
        lines = transcript_text.split("\n")
        chunks = []
        current = []
        current_len = 0
        for line in lines:
            if current_len + len(line) > MAX_CHUNK and current:
                chunks.append("\n".join(current))
                current = [line]
                current_len = len(line)
            else:
                current.append(line)
                current_len += len(line)
        if current:
            chunks.append("\n".join(current))
        
        try:
            llm = get_llm()
            
            async def generate():
                # Step 1: 逐块总结
                chunk_summaries = []
                for i, chunk in enumerate(chunks):
                    p = f"请用一段话（不超过300字）总结以下会议片段的核心内容：\n\n{chunk}"
                    try:
                        partial = await llm.generate(p, max_tokens=400, timeout=300)
                        chunk_summaries.append(f"[片段{i+1}] {partial}")
                    except Exception as e:
                        chunk_summaries.append(f"[片段{i+1} 总结失败: {e}]")
                    progress_msg = f"[分块总结 {i+1}/{len(chunks)} 完成]\n"
                    yield f"data: {json.dumps({'token': progress_msg})}\n\n"
                
                # Step 2: 汇总
                combined = "\n\n".join(chunk_summaries)
                
                # 动态调整：如果汇总后还太长
                if len(combined) > MAX_CHUNK:
                    combined = combined[:MAX_CHUNK] + "\n[... 汇总文本截断 ...]"
                
                summary_prompt = f"""请根据以下片段总结，按照要求整理完整会议纪要。

要求：
{request.prompt}

片段总结：
{combined}"""
                
                final = await llm.generate(summary_prompt, max_tokens=1500, timeout=300)
                
                yield f"data: {json.dumps({'token': final})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"
        except RuntimeError as e:
            raise HTTPException(status_code=409, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
        return StreamingResponse(generate(), media_type="text/event-stream")
    
    # 短文本走原逻辑
    prompt = f"""请根据以下带时间戳和发言人的转录文本，按照要求整理纪要。

要求：
{request.prompt}

内容：
{transcript_text}"""
    
    try:
        llm = get_llm()
        
        async def generate():
            full_response = []
            async for token in llm.generate_stream(prompt, max_tokens=1500, timeout=600):
                full_response.append(token)
                yield f"data: {json.dumps({'token': token})}\n\n"
            
            complete_text = ''.join(full_response)
            AudioFileModel.update_summary(request.audio_file_id, complete_text)
            yield f"data: {json.dumps({'done': True})}\n\n"
        
        return StreamingResponse(generate(), media_type="text/event-stream")
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def chat_with_transcript(request: ChatRequest):
    project = ProjectModel.get_by_id(request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    transcript_text = TranscriptModel.get_all_text_by_project(request.project_id)

    # 如果提供了发言人名称映射，替换文本中的"发言人 X"
    if request.speaker_names:
        for sid, name in request.speaker_names.items():
            if name and name.strip():
                transcript_text = transcript_text.replace(f"发言人 {sid}", name.strip())
    
    # 问答场景：优先用最近内容 + 截断
    MAX_CHARS = 3000
    if len(transcript_text) > MAX_CHARS:
        transcript_text = transcript_text[:MAX_CHARS] + "\n[... 文本过长，仅显示前半部分 ...]"
    
    system_prompt = f"""你是一个智能助手，可以帮助用户理解和分析转录内容。

以下是项目"{project.name}"的转录内容：
{transcript_text}

请基于这些转录内容回答用户的问题。如果问题超出转录内容范围，请如实告知。"""
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # 加载历史记录
    if request.history:
        history = request.history[-(request.max_context * 2):]
        messages.extend(history)
    else:
        # 从数据库加载历史
        db_history = AIChatModel.get_by_project(request.project_id, limit=request.max_context * 2)
        for chat in db_history:
            messages.append({"role": chat.role, "content": chat.content})
    
    messages.append({"role": "user", "content": request.question})
    
    # 保存用户问题
    AIChatModel.create(request.project_id, "user", request.question)
    
    try:
        llm = get_llm()
        
        async def generate():
            full_response = []
            async for token in llm.chat_stream(messages, num_ctx=16384, timeout=120):
                full_response.append(token)
                yield f"data: {json.dumps({'token': token})}\n\n"
            
            # 保存AI回答
            complete_text = ''.join(full_response)
            AIChatModel.create(request.project_id, "assistant", complete_text)
            yield f"data: {json.dumps({'done': True})}\n\n"
        
        return StreamingResponse(generate(), media_type="text/event-stream")
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/history/{project_id}")
async def get_chat_history(project_id: int, limit: int = 50):
    project = ProjectModel.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    chats = AIChatModel.get_by_project(project_id, limit)
    
    return [
        {
            "id": c.id,
            "role": c.role,
            "content": c.content,
            "created_at": c.created_at
        }
        for c in chats
    ]


def format_transcript_for_llm(segments, speaker_names: dict = None) -> str:
    """格式化转写段落供 LLM 使用。speaker_names: {"0": "张总", "1": "李工"}"""
    lines = []
    for s in segments:
        start_min = int(s.start_time // 60)
        start_sec = int(s.start_time % 60)
        end_min = int(s.end_time // 60)
        end_sec = int(s.end_time % 60)

        # 优先用自定义名称，回退到默认编号
        sid = str(s.speaker_id)
        name = (speaker_names or {}).get(sid) or f"发言人 {sid}"

        lines.append(
            f"[{start_min:02d}:{start_sec:02d}-{end_min:02d}:{end_sec:02d}] "
            f"{name}: {s.text}"
        )
    
    return "\n\n".join(lines)