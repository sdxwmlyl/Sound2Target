"""
S2T 会议转写健壮流水线
解决 stop_recording 超时、转写卡死、数据库锁死等已知问题
用法: python pipeline.py <project_id> <session_id> <audio_file_id>
"""
import sys, time, json, sqlite3, requests

BASE = "http://localhost:8000"
DB = r"d:\projectsound2target\S2T\backend\data\s2t.db"

def check(audio_id):
    """检查音频状态"""
    r = requests.get(f"{BASE}/api/audio-files/{audio_id}")
    d = r.json()
    return d["status"], d.get("error_message"), d.get("char_count", 0)

def reset_db(audio_id):
    """重置卡死的音频状态"""
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE audio_files SET status='completed', error_message=NULL WHERE id=?", (audio_id,))
    conn.commit()
    conn.close()

def trigger_transcribe(audio_id):
    """触发转写，如遇 processing 则重置后重试"""
    for attempt in range(3):
        r = requests.post(f"{BASE}/api/transcribe", json={"audio_file_id": audio_id})
        if r.status_code == 200:
            return True, r.json()
        if "already being processed" in r.text:
            print(f"  转写卡死，重置数据库 (第{attempt+1}次)")
            reset_db(audio_id)
            time.sleep(2)
        else:
            return False, r.text
    return False, "重试3次均失败"

def wait_transcribe(audio_id, max_wait=1800):
    """等待转写完成，每30秒检查"""
    start = time.time()
    while time.time() - start < max_wait:
        status, err, chars = check(audio_id)
        if status == "completed" and chars > 0:
            return True, chars
        if status == "failed":
            return False, err
        print(f"  转写中... ({int(time.time()-start)}s)")
        time.sleep(30)
    return False, "超时"

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python pipeline.py <project_id> <session_id> <audio_file_id>")
        sys.exit(1)
    
    project_id = int(sys.argv[1])
    session_id = sys.argv[2]
    audio_id = int(sys.argv[3])
    
    # Step 1: 检查状态，如已完成则直接返回
    status, err, chars = check(audio_id)
    print(f"初始状态: {status}, 字数: {chars}")
    
    if status == "completed" and chars > 0:
        print("✅ 转写已完成，无需重新处理")
        print(json.dumps({"ok": True, "audio_id": audio_id, "chars": chars, "project_id": project_id}))
        sys.exit(0)
    
    # Step 2: 触发转写
    print("触发转写...")
    ok, result = trigger_transcribe(audio_id)
    if not ok:
        print(f"❌ 触发失败: {result}")
        sys.exit(1)
    print(f"  转写已启动: {result}")
    
    # Step 3: 等待完成
    print("等待转写完成...")
    ok, result = wait_transcribe(audio_id)
    if ok:
        print(f"✅ 转写完成: {result} 字")
        print(json.dumps({"ok": True, "audio_id": audio_id, "chars": result, "project_id": project_id}))
    else:
        print(f"❌ 转写失败: {result}")
        sys.exit(1)
