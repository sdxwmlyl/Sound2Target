"""
启动后台录音（DETACHED_PROCESS，不会随 shell 超时被杀）。
用法: python start_bg_recording.py <project_id> <audio_name> [hotwords]

返回: 输出的第一行 JSON 包含 session_id / audio_file_id
"""

import subprocess, sys, time, os, json

if len(sys.argv) < 3:
    print('Usage: python start_bg_recording.py <project_id> <audio_name> [hotwords]')
    sys.exit(1)

project_id = sys.argv[1]
audio_name = sys.argv[2]
hotwords = sys.argv[3] if len(sys.argv) > 3 else ''

ws_recorder = r'd:\projectsound2target\ws_recorder.py'
python = r'D:\QwenPaw\python.exe'

cmd = [python, ws_recorder, 'start', project_id, audio_name]
if hotwords:
    cmd.append(hotwords)

proc = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
    text=True
)

# Wait for first JSON output line (最多 15 秒)
start = time.time()
output = ''
while time.time() - start < 15:
    line = proc.stdout.readline() if proc.stdout else ''
    if line:
        line = line.strip()
        output = line
        try:
            result = json.loads(line)
            if result.get('status') == 'started':
                print(line)  # 输出 JSON 供调用方解析
                sys.exit(0)
            elif result.get('status') == 'error':
                print(line)
                sys.exit(1)
        except json.JSONDecodeError:
            continue

# 超时，打印原始输出
print(json.dumps({'status': 'timeout', 'output': output[:200]}))
sys.exit(1)
