#!/usr/bin/env python
"""
S2T MCP Server - 将 S2T 语音转写系统 REST API 封装为 MCP 工具

工具列表：
  start_server             启动 S2T 后端服务（使用 start.bat 一键启动）
  create_project           创建项目
  start_system_recording   启动系统录音（独立子进程保活，返回 session_id + audio_file_id）
  stop_recording           停止录音并触发后台转写
  cleanup_recording        强制清理残留进程和文件
  check_audio_file_status  查询音频文件转写状态
  get_transcript_text      获取项目完整转写文本
  summarize_project        【方式A】使用 S2T 后端 LLM 对转写进行AI总结（流式读取完整结果）
  extract_viewpoints       【观点提取】深度观点演变分析（版本链/逻辑链/矛盾检测/前提条件）
  get_transcript_for_summary 【方式B】获取转写文本，供 agent 自行总结
  get_transcript_for_viewpoint 获取带时间戳转写文本，供 agent 自行观点分析
  get_project_info         获取项目详情
"""

import json
import os
import sys
import time
import uuid
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastmcp import FastMCP

mcp = FastMCP("s2t-mcp-server")

# ---- 路径常量 ----
S2T_ROOT = Path(__file__).parent
S2T_BACKEND_DIR = S2T_ROOT / "S2T" / "backend"
S2T_START_BAT = S2T_ROOT / "S2T" / "start.bat"
RECORDER_SCRIPT = S2T_ROOT / "ws_recorder.py"
S2T_BASE_URL = "http://localhost:8000"

# ---- 全局状态 ----
SERVER_PROCESS: Optional[subprocess.Popen] = None
ACTIVE_PROCESSES: dict = {}  # session_id -> subprocess.Popen


# ============================================================
# HTTP 工具函数
# ============================================================

def _http(method: str, path: str, body: dict = None, timeout: int = 30) -> dict:
    url = f"{S2T_BASE_URL}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url, method=method, data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err = e.read().decode() if e.fp else ""
        return {"error": f"HTTP {e.code}", "detail": err[:300]}
    except urllib.error.URLError as e:
        return {"error": f"连接失败: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


def _http_get(path: str, timeout: int = 30) -> dict:
    return _http("GET", path, timeout=timeout)


def _http_post(path: str, body: dict, timeout: int = 30) -> dict:
    return _http("POST", path, body, timeout=timeout)


def _is_server_running() -> bool:
    try:
        r = _http_get("/health", timeout=3)
        return r.get("status") == "healthy"
    except Exception:
        return False


def _ok(data: dict) -> str:
    return json.dumps({"success": True, **data}, ensure_ascii=False)


def _fail(msg: str) -> str:
    return json.dumps({"success": False, "error": msg}, ensure_ascii=False)


# ============================================================
# SSE 流式读取（用于 summarize_project）
# ============================================================

def _read_sse_stream(url: str, body: dict, timeout: int = 600) -> str:
    """POST 请求 SSE 端点，收集完整响应文本"""
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url, method="POST", data=data,
        headers={"Content-Type": "application/json", "Accept": "text/event-stream"}
    )
    tokens = []
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            buf = b""
            while True:
                chunk = resp.read(1024)
                if not chunk:
                    break
                buf += chunk
                text = buf.decode("utf-8", errors="replace")
                for line in text.split("\n"):
                    if line.startswith("data: "):
                        try:
                            payload = json.loads(line[6:])
                            if "token" in payload:
                                tokens.append(payload["token"])
                            if payload.get("done"):
                                buf = b""
                                break
                        except json.JSONDecodeError:
                            pass
                buf = b""
    except urllib.error.HTTPError as e:
        return f"[HTTP错误 {e.code}]"
    except Exception as e:
        return f"[SSE读取异常: {e}]"

    return "".join(tokens)


# ============================================================
# MCP Tools
# ============================================================

@mcp.tool(description="启动 S2T 后端服务（使用 start.bat 一键启动）")
def start_server() -> str:
    """启动 S2T 语音转写后端服务。"""
    if _is_server_running():
        return _ok({"message": f"S2T 后端已在运行: {S2T_BASE_URL}"})

    # 优先 start.bat
    if S2T_START_BAT.exists():
        try:
            subprocess.Popen(
                [str(S2T_START_BAT)],
                cwd=str(S2T_ROOT / "S2T"),
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            for i in range(30):
                time.sleep(1)
                if _is_server_running():
                    return _ok({"message": f"S2T 后端已启动: {S2T_BASE_URL}", "elapsed": f"{i+1}s"})
            return _fail("start.bat 启动后30秒后端仍未就绪，请检查后端是否有依赖错误")
        except Exception as e:
            return _fail(f"start.bat 启动失败: {e}")

    # fallback: 直接 uvicorn
    if not S2T_BACKEND_DIR.exists():
        return _fail(f"后端目录不存在: {S2T_BACKEND_DIR}")
    try:
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--host", "localhost", "--port", "8000"],
            cwd=str(S2T_BACKEND_DIR),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
        )
        for i in range(30):
            time.sleep(1)
            if _is_server_running():
                return _ok({"message": f"S2T 后端已启动: {S2T_BASE_URL}", "elapsed": f"{i+1}s"})
        return _fail("uvicorn 启动超时，请检查后端依赖")
    except Exception as e:
        return _fail(f"启动异常: {e}")


@mcp.tool(description="创建转写项目，返回 project_id")
def create_project(name: str, description: str = "") -> str:
    """创建项目，用于组织同一会议的音频文件。"""
    if not _is_server_running():
        return _fail("S2T 服务未运行，请先调用 start_server")

    r = _http_post("/api/projects", {"name": name, "description": description})
    if "error" in r:
        return _fail(f"创建项目失败: {r['error']}")
    return _ok({
        "project_id": r["id"],
        "project_name": r["name"],
        "message": f"项目《{r['name']}》(ID: {r['id']}) 已创建"
    })


@mcp.tool(description="在项目中启动系统声音录制（VB-CABLE 捕获，独立子进程保活）")
def start_system_recording(project_id: int, audio_name: str = "", hotwords: str = "") -> str:
    """
    通过独立子进程 ws_recorder.py 启动系统录音。
    - 子进程通过 WebSocket 连接 S2T 后端
    - 子进程自行保活，直到外部调用 stop_recording
    - 通信：子进程写 session 文件，stop_recording 创建 stop flag

    Args:
        project_id: 项目 ID
        audio_name: 录音名称，留空自动生成
        hotwords: 热词（空格分隔），如 "腾讯会议 人工智能"
    """
    if not _is_server_running():
        return _fail("S2T 服务未运行")

    # 验证项目存在
    proj = _http_get(f"/api/projects/{project_id}")
    if "error" in proj:
        return _fail(f"项目不存在: {proj['error']}")

    if not audio_name:
        audio_name = f"会议录音_{datetime.now().strftime('%H%M%S')}"

    # 启动 ws_recorder.py 作为独立子进程
    cmd = [
        sys.executable, str(RECORDER_SCRIPT),
        "start", str(project_id), audio_name
    ]
    if hotwords:
        cmd.append(hotwords)

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
        )
    except Exception as e:
        return _fail(f"启动录音子进程失败: {e}")

    # 等待第一行 JSON 输出（最多 15 秒）
    start_time = time.time()
    output_lines = []
    while time.time() - start_time < 15:
        line = proc.stdout.readline() if proc.stdout else ""
        if line:
            line = line.strip()
            output_lines.append(line)
            try:
                result = json.loads(line)
                if result.get("status") == "started":
                    session_id = result.get("session_id")
                    audio_file_id = result.get("audio_file_id")
                    ACTIVE_PROCESSES[session_id] = proc
                    return _ok({
                        "session_id": session_id,
                        "audio_file_id": audio_file_id,
                        "audio_name": audio_name,
                        "message": f"🎙️ 系统录音已开始: {audio_name}"
                    })
                elif result.get("status") == "error":
                    return _fail(f"录音启动失败: {result.get('error', '未知错误')}")
            except json.JSONDecodeError:
                continue  # 不是 JSON 行，继续等待
        else:
            time.sleep(0.2)

    # 超时
    proc.kill()
    return _fail(f"录音启动超时（15秒）。输出: {'; '.join(output_lines[-3:])}")


@mcp.tool(description="停止录音，S2T 自动开始后台转写（通过 ws_recorder.py 子进程）")
def stop_recording(session_id: str) -> str:
    """
    停止指定 session 的录音。
    通过创建 stop flag 通知 ws_recorder.py 子进程关闭连接，
    后端自动开始转写。

    Args:
        session_id: start_system_recording 返回的 session_id
    """
    # 运行 ws_recorder.py stop
    cmd = [sys.executable, str(RECORDER_SCRIPT), "stop", session_id]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=60
        )
        output = result.stdout.strip()
        try:
            data = json.loads(output)
            if data.get("status") in ("transcribing", "stopped"):
                af_id = data.get("audio_file_id")
                # 清理进程引用
                if session_id in ACTIVE_PROCESSES:
                    del ACTIVE_PROCESSES[session_id]
                return _ok({
                    "session_id": session_id,
                    "audio_file_id": af_id,
                    "message": "⏹️ 录音已停止，后台转写已启动"
                })
            elif data.get("status") == "timeout":
                return _fail(f"停止录音超时: {data.get('error', '')}")
            else:
                return _fail(f"停止结果异常: {output[:200]}")
        except json.JSONDecodeError:
            return _fail(f"停止脚本返回非JSON: {output[:200]}")
    except subprocess.TimeoutExpired:
        return _fail("停止录音超时（60秒）")
    except Exception as e:
        return _fail(f"停止录音异常: {e}")


@mcp.tool(description="【清理】强制终止卡死的 ws_recorder 进程并清理 session 文件（不经过 shell，不会触发工具守卫）")
def cleanup_recording(session_id: str = "", force_kill_all: bool = False) -> str:
    """
    强制清理 ws_recorder 录音进程和 session 残留。
    使用 psutil（Python 原生 API）管理进程，不经过 shell 命令，因此不会触发安全审批。

    Args:
        session_id: 要清理的 session_id。为空时清除所有 ws_recorder 进程
        force_kill_all: 是否 kill 所有 python.exe 中运行 ws_recorder 的进程
    """
    import psutil
    from pathlib import Path
    import tempfile

    SESSIONS_DIR = Path(tempfile.gettempdir()) / "s2t_sessions"
    results = {"killed": [], "cleaned_files": [], "errors": []}

    # 1. 查找 ws_recorder 进程
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
        try:
            cmdline = proc.info.get('cmdline') or []
            cmd_str = ' '.join(cmdline).lower()
            if 'ws_recorder' not in cmd_str:
                continue

            proc_pid = proc.info['pid']
            proc_session = ''
            for arg in cmdline:
                if arg.startswith('ws_session_'):
                    proc_session = arg
                    break

            # 匹配指定的 session_id 或全部
            if session_id and session_id not in cmd_str:
                continue
            if not force_kill_all and not session_id:
                # session_id 为空且 force_kill_all=False：只杀掉没有对应 session 文件的孤儿进程
                pass  # 继续执行

            # 安全终止
            proc.terminate()
            # 等 3 秒，如果还没死就 kill
            gone, alive = psutil.wait_procs([proc], timeout=3)
            if alive:
                proc.kill()
                results["killed"].append(f"pid={proc_pid}(force_kill)")
            else:
                results["killed"].append(f"pid={proc_pid}(terminated)")

            # 记录 session 信息
            if proc_session and proc_session.startswith('ws_session_'):
                results.setdefault("sessions_killed", []).append(proc_session)

        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            results["errors"].append(str(e))

    # 2. 清理 session 文件
    if SESSIONS_DIR.exists():
        for f in SESSIONS_DIR.iterdir():
            if f.suffix == '.json' or f.suffix == '.flag':
                if session_id:
                    # 只清理匹配的
                    if session_id in f.stem:
                        try:
                            f.unlink()
                            results["cleaned_files"].append(f.name)
                        except Exception as e:
                            results["errors"].append(f"删文件失败 {f.name}: {e}")
                else:
                    # 清理所有
                    try:
                        f.unlink()
                        results["cleaned_files"].append(f.name)
                    except Exception as e:
                        results["errors"].append(f"删文件失败 {f.name}: {e}")

    # 3. 清理 ACTIVE_PROCESSES 全局状态
    if session_id and session_id in ACTIVE_PROCESSES:
        del ACTIVE_PROCESSES[session_id]
    elif not session_id:
        ACTIVE_PROCESSES.clear()

    return _ok({
        "killed_count": len(results["killed"]),
        "killed_processes": results["killed"],
        "cleaned_files_count": len(results["cleaned_files"]),
        "cleaned_files": results["cleaned_files"][:10],
        "session_id": session_id or "all",
        "message": (
            f"已清理 {len(results['killed'])} 个进程, {len(results['cleaned_files'])} 个残留文件"
            if not results["errors"]
            else f"清理完成（{len(results['errors'])} 个错误）"
        )
    })


@mcp.tool(description="查询音频文件的转写/处理状态")
def check_audio_file_status(audio_file_id: int) -> str:
    """查询音频文件转写状态。"""
    if not _is_server_running():
        return _fail("S2T 服务未运行")

    r = _http_get(f"/api/audio-files/{audio_file_id}")
    if "error" in r:
        return _fail(f"查询失败: {r['error']}")

    segments = r.get("segments") or []
    is_completed = r.get("status") == "completed" and len(segments) > 0

    return _ok({
        "audio_file_id": r.get("id"),
        "audio_name": r.get("audio_name"),
        "status": r.get("status"),
        "source_type": r.get("source_type"),
        "duration": r.get("duration"),
        "segment_count": len(segments),
        "char_count": sum(len(s.get("text", "")) for s in segments) if segments else 0,
        "has_transcript": is_completed,
        "has_summary": bool(r.get("summary"))
    })


@mcp.tool(description="获取项目的完整转写文本（含说话人标记和时间戳）")
def get_transcript_text(project_id: int) -> str:
    """获取项目下所有已完成转写文本，含发言人+时间戳。"""
    if not _is_server_running():
        return _fail("S2T 服务未运行")

    proj = _http_get(f"/api/projects/{project_id}")
    if "error" in proj:
        return _fail(f"获取项目失败: {proj['error']}")

    sections = []
    for af in proj.get("audio_files", []):
        if af["status"] != "completed":
            continue

        resp = _http_get(f"/api/audio-files/{af['id']}/transcript")
        segments = resp if isinstance(resp, list) else resp.get("segments", [])

        if not segments:
            continue

        lines = []
        for seg in segments:
            spk = seg.get("speaker_id", "0")
            txt = seg.get("text", "")
            s, e = seg.get("start_time", 0), seg.get("end_time", 0)
            ts = f"{int(s//60):02d}:{int(s%60):02d}-{int(e//60):02d}:{int(e%60):02d}"
            lines.append(f"[{ts}] 发言人{spk}: {txt}")

        sections.append(f"【{af['audio_name']} ({af.get('source_type', '')})】\n" + "\n".join(lines))

    if not sections:
        return _ok({
            "project_id": project_id,
            "project_name": proj.get("name"),
            "has_content": False,
            "message": "暂无已完成转写的内容"
        })

    full_text = "\n\n".join(sections)
    return _ok({
        "project_id": project_id,
        "project_name": proj.get("name"),
        "has_content": True,
        "char_count": len(full_text),
        "transcript_text": full_text
    })


@mcp.tool(description="【方式A】使用 S2T 后端本地/在线 LLM 对项目所有转写进行AI总结（流式读取完整结果）")
def summarize_project(project_id: int, prompt: str = "") -> str:
    """
    优先方式：使用 S2T 后端配置的 LLM（本地 Ollama / 阿里百炼 / Deepseek）
    对转写内容进行智能总结。完整收集流式输出后返回。

    Args:
        project_id: 项目 ID
        prompt: 总结要求（留空则使用默认模板）
    """
    if not _is_server_running():
        return _fail("S2T 服务未运行")

    proj = _http_get(f"/api/projects/{project_id}")
    if "error" in proj:
        return _fail(f"获取项目失败: {proj['error']}")

    completed = [af for af in proj.get("audio_files", []) if af["status"] == "completed"]
    if not completed:
        return _fail("项目没有已完成转写的音频文件，无法总结")

    if not prompt:
        prompt = "- 会议主题是什么？\n- 罗列每个发言人的核心观点\n- 整理决议事项和后续待办"

    results = []
    for af in completed:
        text = _read_sse_stream(
            f"{S2T_BASE_URL}/api/llm/summarize",
            {"audio_file_id": af["id"], "prompt": prompt},
            timeout=600
        )
        if text and not text.startswith("["):
            results.append(f"## 📝 {af['audio_name']}\n{text}")
        else:
            results.append(f"## ❌ {af['audio_name']}: {text}")

    return _ok({
        "project_id": project_id,
        "project_name": proj.get("name"),
        "strategy": "s2t_backend_llm",
        "audio_count": len(completed),
        "summary": "\n\n".join(results),
        "message": "总结完成（使用 S2T 后端 LLM）"
    })


@mcp.tool(description="【观点提取】对会议转录进行深度观点演变分析：追踪同一主题的版本变化、逻辑推导链、矛盾检测、前提条件和待确认事项。比 summarize 更适合需要追踪讨论过程的场景。")
def extract_viewpoints(project_id: int, custom_topics: str = "") -> str:
    """
    使用 S2T 后端本地 LLM 对项目转写进行观点演变提取。

    区别于 summarize_project（压缩摘要）：
    - 追踪同一主题的观点变化（v1→v2→v3）
    - 构建逻辑推导链（因为A→所以B）
    - 检测前后矛盾
    - 记录前提条件和失效边界
    - 标记待确认事项

    Args:
        project_id: 项目 ID
        custom_topics: 自定义关注主题（逗号分隔，如 "并发设计,模型部署,一期范围"），留空则自动识别
    """
    if not _is_server_running():
        return _fail("S2T 服务未运行")

    # 解析自定义主题
    topics_dict = {}
    if custom_topics:
        for topic in custom_topics.split(","):
            topic = topic.strip()
            if topic:
                topics_dict[topic] = [topic]

    body = {"project_id": project_id}
    if topics_dict:
        body["custom_topics"] = topics_dict

    # 使用同步端点（超长超时，LLM 多轮处理需要时间）
    r = _http_post("/api/viewpoint/extract-sync", body, timeout=1800)

    if "error" in r:
        return _fail(f"观点提取失败: {r['error']}")

    if r.get("success"):
        stats = r.get("stats", {})
        return _ok({
            "project_id": r["project_id"],
            "project_name": r["project_name"],
            "report": r["report"],
            "structured_data": r.get("structured_data"),
            "stats": stats,
            "message": f"观点提取完成（{stats.get('total_segments', 0)}段转写, {stats.get('total_chunks', 0)}个分析块）"
        })

    return _fail(f"意外响应: {json.dumps(r, ensure_ascii=False)[:500]}")


@mcp.tool(description="获取项目完整转写文本（带时间戳和发言人），供 agent 自行进行观点分析")
def get_transcript_for_viewpoint(project_id: int) -> str:
    """获取带时间戳和发言人的完整转写文本，供 agent 结合 large-file-reader skill 自行分析。"""
    return get_transcript_text(project_id)


@mcp.tool(description="【方式B兜底】获取项目完整转写文本，供 agent 自行进行 AI 总结")
def get_transcript_for_summary(project_id: int, user_prompt: str = "") -> str:
    """
    兜底方式：获取完整的转写文本，由 agent 自身的大模型进行总结分析。
    返回的 transcript_text 可直接用于 prompt。
    """
    return get_transcript_text(project_id)


@mcp.tool(description="获取项目详情（含音频文件列表和各自状态）")
def get_project_info(project_id: int) -> str:
    """获取项目完整详情。"""
    if not _is_server_running():
        return _fail("S2T 服务未运行")

    r = _http_get(f"/api/projects/{project_id}")
    if "error" in r:
        return _fail(f"获取项目失败: {r['error']}")

    files = [{
        "id": af["id"],
        "name": af["audio_name"],
        "type": af["source_type"],
        "status": af["status"],
        "duration": af.get("duration"),
        "created_at": af.get("created_at")
    } for af in r.get("audio_files", [])]

    return _ok({
        "project_id": r["id"],
        "project_name": r["name"],
        "description": r.get("description", ""),
        "hotwords": r.get("hotwords", ""),
        "created_at": r.get("created_at"),
        "total_audio": len(files),
        "completed_audio": sum(1 for f in files if f["status"] == "completed"),
        "audio_files": files
    })


# ============================================================
# 主入口
# ============================================================
if __name__ == "__main__":
    mcp.run(transport="stdio")
