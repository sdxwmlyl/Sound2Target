#!/usr/bin/env python
"""
S2T WebSocket 录音保活脚本。
通过后台进程维持 WebSocket 长连接，确保录音不被中断。
用法:
  python ws_recorder.py start <project_id> [audio_name] [hotwords]
  python ws_recorder.py stop <session_id>

通信机制：
  - start: 在 temp dir 写入 session 信息文件
  - stop: 读取 session 文件 → 发送 stop → 清理
"""

import sys
import json
import asyncio
import os
import time
import uuid
import signal
import tempfile
from pathlib import Path
from datetime import datetime

S2T_BASE = "http://localhost:8000"
SESSIONS_DIR = Path(tempfile.gettempdir()) / "s2t_sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def session_file(session_id: str) -> Path:
    return SESSIONS_DIR / f"{session_id}.json"


def save_session(session_id: str, data: dict):
    session_file(session_id).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def load_session(session_id: str) -> dict:
    f = session_file(session_id)
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    return {}


def delete_session(session_id: str):
    f = session_file(session_id)
    if f.exists():
        f.unlink()


# ============================================================

async def _start_recording(project_id: int, audio_name: str, hotwords: str):
    """WebSocket 连接 → 启动录音 → 保活 → 等待停止信号"""
    import websockets

    session_id = f"ws_session_{uuid.uuid4().hex[:12]}"
    ws_url = f"ws://localhost:8000/api/realtime/ws/{project_id}?session_id={session_id}"

    # 创建信号文件
    stop_flag = SESSIONS_DIR / f"stop_{session_id}.flag"

    async with websockets.connect(ws_url, ping_interval=None) as ws:
        # 1. 等 connected
        msg = json.loads(await asyncio.wait_for(ws.recv(), 10))
        assert msg.get("type") == "connected", f"连接异常: {msg}"

        # 2. 发 start_recording
        await ws.send(json.dumps({
            "type": "start_recording",
            "source_type": "system",
            "audio_name": audio_name,
            "hotwords": hotwords
        }))

        # 3. 等确认
        ack = json.loads(await asyncio.wait_for(ws.recv(), 15))
        assert ack.get("type") == "recording_started", f"启动失败: {ack}"

        audio_file_id = ack.get("audio_file_id")

        # 4. 写入 session 信息（给外部进程读取）
        save_session(session_id, {
            "session_id": session_id,
            "project_id": project_id,
            "audio_file_id": audio_file_id,
            "audio_name": audio_name,
            "status": "recording",
            "started_at": datetime.now().isoformat(),
            "ws_url": ws_url
        })

        # 输出到 stdout 供调用方解析
        print(json.dumps({
            "status": "started",
            "session_id": session_id,
            "audio_file_id": audio_file_id
        }))
        sys.stdout.flush()

        # 5. 保活循环
        while True:
            # 检查停止信号
            if stop_flag.exists():
                await ws.send(json.dumps({"type": "stop_recording"}))
                try:
                    confirm = json.loads(await asyncio.wait_for(ws.recv(), 15))
                    if confirm.get("type") in ("recording_stopped",):
                        pass
                except Exception:
                    pass
                save_session(session_id, {
                    **load_session(session_id),
                    "status": "transcribing"
                })
                stop_flag.unlink(missing_ok=True)
                print(json.dumps({"status": "stopped", "session_id": session_id}))
                sys.stdout.flush()
                return

            # 接收消息（带心跳）
            try:
                data = json.loads(await asyncio.wait_for(ws.recv(), timeout=30))
                if data.get("type") == "recording_stopped":
                    # 后端主动停止
                    save_session(session_id, {
                        **load_session(session_id),
                        "status": "transcribing"
                    })
                    stop_flag.unlink(missing_ok=True)
                    return
                elif data.get("type") == "error":
                    save_session(session_id, {
                        **load_session(session_id),
                        "status": "error",
                        "error": data.get("message", "")
                    })
                    return
            except asyncio.TimeoutError:
                try:
                    await ws.send(json.dumps({"type": "ping"}))
                except Exception:
                    break
            except Exception:
                break


# ============================================================

async def _stop_recording(session_id: str):
    """设置停止信号，让保活进程自行关闭"""
    stop_flag = SESSIONS_DIR / f"stop_{session_id}.flag"
    stop_flag.write_text("1")

    # 等待状态更新
    for _ in range(80):  # 最多等40秒（ws_recorder确认stop_recording最长15秒）
        await asyncio.sleep(0.5)
        info = load_session(session_id)
        if info.get("status") in ("transcribing", "stopped", "error"):
            print(json.dumps({
                "status": info.get("status", "stopped"),
                "session_id": session_id,
                "audio_file_id": info.get("audio_file_id"),
            }))
            sys.stdout.flush()
            return

    print(json.dumps({"status": "timeout", "session_id": session_id, "error": "停止确认超时"}))
    sys.stdout.flush()


# ============================================================

def main():
    if len(sys.argv) < 2:
        print("用法: python ws_recorder.py start <project_id> [audio_name] [hotwords]")
        print("  或: python ws_recorder.py stop <session_id>")
        sys.exit(1)

    action = sys.argv[1]

    if action == "start":
        if len(sys.argv) < 3:
            print('{"status":"error","error":"缺少 project_id"}')
            sys.exit(1)
        project_id = int(sys.argv[2])
        audio_name = sys.argv[3] if len(sys.argv) > 3 else f"会议录音_{datetime.now().strftime('%H%M%S')}"
        hotwords = sys.argv[4] if len(sys.argv) > 4 else ""

        try:
            asyncio.run(_start_recording(project_id, audio_name, hotwords))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(json.dumps({"status": "error", "error": str(e)}))
            sys.stdout.flush()

    elif action == "stop":
        if len(sys.argv) < 3:
            print('{"status":"error","error":"缺少 session_id"}')
            sys.exit(1)
        session_id = sys.argv[2]
        try:
            asyncio.run(_stop_recording(session_id))
        except Exception as e:
            print(json.dumps({"status": "error", "error": str(e)}))
            sys.stdout.flush()

    else:
        print(f'{{"status":"error","error":"未知操作: {action}"}}')
        sys.exit(1)


if __name__ == "__main__":
    main()
