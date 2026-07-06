#!/usr/bin/env python
"""
会议后处理脚本：
1. 检查录音 session 状态
2. 停止录音 → 触发转写
3. 轮询转写状态直到完成
4. 获取转写全文
5. AI 总结
6. 写入结果文件

用法: python meeting_postprocess.py <session_id> [project_id]
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import json
import time
import subprocess
import urllib.request
import os
from pathlib import Path
from datetime import datetime

S2T_BASE = "http://localhost:8000"
RECORDER_SCRIPT = Path(__file__).parent / "ws_recorder.py"
RESULT_DIR = Path(__file__).parent / "meeting_results"
RESULT_DIR.mkdir(exist_ok=True)


def http_get(path):
    url = f"{S2T_BASE}{path}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}


def run_recorder(args):
    cmd = [sys.executable, str(RECORDER_SCRIPT)] + args
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
    try:
        return json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        return {"error": f"非JSON输出: {result.stdout[:200]}"}


def read_sse_stream(url, body, timeout=600):
    import urllib.parse
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
    except Exception as e:
        return f"[SSE错误: {e}]"
    return "".join(tokens)


def postprocess(session_id: str, project_id: int = None):
    print(f"\n{'='*60}")
    print(f"📋 会议后处理开始 | session={session_id}")
    print(f"时间: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}\n")

    # Step 1: 停止录音
    print("Step 1/5: ⏹️ 停止录音...")
    stop_result = run_recorder(["stop", session_id])
    print(f"  结果: {json.dumps(stop_result, ensure_ascii=False)}")

    if "error" in stop_result:
        print(f"❌ 停止失败: {stop_result['error']}")
        return

    audio_file_id = stop_result.get("audio_file_id")

    # Step 2: 如果没有 project_id，从 session 文件获取
    import tempfile
    session_file = Path(tempfile.gettempdir()) / "s2t_sessions" / f"{session_id}.json"
    if session_file.exists():
        session_data = json.loads(session_file.read_text(encoding="utf-8"))
        project_id = project_id or session_data.get("project_id")
        audio_file_id = audio_file_id or session_data.get("audio_file_id")

    print(f"  项目ID: {project_id}, 音频文件ID: {audio_file_id}")

    if not project_id:
        print("❌ 无法确定 project_id")
        return

    # Step 3: 轮询转写状态
    print(f"\nStep 2/5: ⏳ 等待转写完成...")
    max_wait = 600  # 最多等10分钟
    start_ts = time.time()
    completed = False

    if audio_file_id:
        while time.time() - start_ts < max_wait:
            status = http_get(f"/api/audio-files/{audio_file_id}")
            s = status.get("status")
            segments = status.get("segments") or []
            char_count = sum(len(s.get("text", "")) for s in segments) if segments else 0
            elapsed = int(time.time() - start_ts)
            print(f"  [{elapsed}s] 状态: {s}, 段落数: {len(segments)}, 字符: {char_count}")

            if s == "completed" and len(segments) > 0:
                completed = True
                print(f"  ✅ 转写完成! 共 {len(segments)} 段, {char_count} 字")
                break
            elif s == "error":
                print(f"  ❌ 转写出错")
                break

            time.sleep(10)

    if not completed:
        print("⚠️ 转写未完成，尝试获取已有内容...")

    # Step 4: 获取转写全文
    print(f"\nStep 3/5: 📝 获取转写全文...")
    proj = http_get(f"/api/projects/{project_id}")
    if "error" not in proj:
        sections = []
        for af in proj.get("audio_files", []):
            if af["status"] != "completed":
                continue
            resp = http_get(f"/api/audio-files/{af['id']}/transcript")
            segs = resp if isinstance(resp, list) else resp.get("segments", [])
            lines = []
            for seg in segs:
                spk = seg.get("speaker_id", "0")
                txt = seg.get("text", "")
                s, e = seg.get("start_time", 0), seg.get("end_time", 0)
                ts = f"{int(s//60):02d}:{int(s%60):02d}-{int(e//60):02d}:{int(e%60):02d}"
                lines.append(f"[{ts}] 发言人{spk}: {txt}")
            sections.append(f"【{af['audio_name']}】\n" + "\n".join(lines))

        full_text = "\n\n".join(sections)
        print(f"  全文: {len(full_text)} 字")

        # 保存转写文本
        transcript_file = RESULT_DIR / f"project_{project_id}_transcript.txt"
        transcript_file.write_text(full_text, encoding="utf-8")
        print(f"  已保存: {transcript_file}")
    else:
        full_text = ""
        print(f"  获取失败: {proj.get('error')}")

    # Step 5: AI 总结
    print(f"\nStep 4/5: 🤖 AI 总结...")
    prompt = "- 会议主题是什么？\n- 罗列每个发言人的核心观点\n- 整理决议事项和后续待办"
    
    summary = ""
    if audio_file_id:
        summary = read_sse_stream(
            f"{S2T_BASE}/api/llm/summarize",
            {"audio_file_id": audio_file_id, "prompt": prompt},
            timeout=600
        )
    
    if summary and not summary.startswith("["):
        print(f"✅ AI 总结完成 ({len(summary)} 字)")
    else:
        summary = summary or "（总结不可用）"
        print(f"⚠️  AI总结状态: {summary[:100]}")

    # Step 5/5: 写入结果
    result = {
        "session_id": session_id,
        "project_id": project_id,
        "audio_file_id": audio_file_id,
        "transcript_length": len(full_text),
        "summary_length": len(summary),
        "summary": summary,
        "transcript": full_text[:5000],  # 摘要版
        "completed_at": datetime.now().isoformat()
    }

    result_file = RESULT_DIR / f"project_{project_id}_result.json"
    result_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ 结果已保存: {result_file}")

    # 输出最终结果到 stdout（给 cron/调用方）
    print(f"\n{'='*60}")
    print("📊 最终结果概要")
    print(f"{'='*60}")
    print(f"项目: {proj.get('name', 'N/A')}")
    print(f"转写字数: {len(full_text)}")
    if summary and not summary.startswith("["):
        print(f"\n--- AI 总结 ---\n{summary[:2000]}...")
    
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python meeting_postprocess.py <session_id> [project_id]")
        sys.exit(1)

    session_id = sys.argv[1]
    project_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
    postprocess(session_id, project_id)
