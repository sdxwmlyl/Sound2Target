# API文档

## 基础信息

- Base URL: `http://localhost:8000/api`
- 认证: 无（本地部署）

## 项目管理

### 获取项目列表
```
GET /api/projects
```

**响应：**
```json
[
  {
    "id": 1,
    "name": "项目名称",
    "description": "描述",
    "hotwords": "热词1 热词2",
    "audio_count": 5,
    "completed_count": 3,
    "created_at": "2026-05-23 10:00:00",
    "updated_at": "2026-05-23 10:00:00"
  }
]
```

### 创建项目
```
POST /api/projects
```

**请求体：**
```json
{
  "name": "项目名称",
  "description": "描述"
}
```

### 获取项目详情
```
GET /api/projects/{project_id}
```

### 更新项目
```
PUT /api/projects/{project_id}
```

### 删除项目
```
DELETE /api/projects/{project_id}
```

### 更新热词
```
PUT /api/projects/{project_id}/hotwords
```

**请求体：**
```json
{
  "hotwords": "热词1 热词2 热词3"
}
```

## 音频文件

### 获取项目音频列表
```
GET /api/projects/{project_id}/audio-files
```

**响应：**
```json
[
  {
    "id": 1,
    "audio_name": "音频名称",
    "filename": "file.wav",
    "source_type": "file",
    "duration": 120.5,
    "status": "completed",
    "char_count": 1500,
    "created_at": "2026-05-23 10:00:00"
  }
]
```

### 上传音频文件
```
POST /api/projects/{project_id}/upload
Content-Type: multipart/form-data
```

**参数：**
- `file`: 音频文件
- `audio_name`: 音频名称

### 获取音频详情
```
GET /api/audio-files/{audio_file_id}
```

### 获取转写结果
```
GET /api/audio-files/{audio_file_id}/transcript
```

**响应：**
```json
{
  "audio_file": {
    "id": 1,
    "audio_name": "音频名称",
    "status": "completed",
    "summary": "AI总结内容"
  },
  "segments": [
    {
      "id": 1,
      "speaker_id": "0",
      "start_time": 0.0,
      "end_time": 5.0,
      "text": "转写文本",
      "original_text": "原始文本",
      "edited": false
    }
  ]
}
```

### 编辑转写段落
```
PUT /api/transcript-segments/{segment_id}
```

**请求体：**
```json
{
  "text": "修改后的文本"
}
```

### 停止音频处理
```
POST /api/audio-files/{audio_file_id}/stop
```

### 删除音频
```
DELETE /api/audio-files/{audio_file_id}
```

### 音频流
```
GET /api/audio-files/{audio_file_id}/stream
```

## 实时录音

### WebSocket连接
```
ws://localhost:8000/api/realtime/ws/{project_id}?session_id={session_id}
```

**消息类型：**

开始录音：
```json
{
  "type": "start_recording",
  "source_type": "microphone",
  "hotwords": "热词1 热词2",
  "audio_name": "录音名称"
}
```

停止录音：
```json
{
  "type": "stop_recording"
}
```

**服务器消息：**
```json
{
  "type": "recording_started",
  "audio_file_id": 1
}
```

```json
{
  "type": "recording_stopped",
  "audio_file_id": 1,
  "message": "录音已停止，正在后台转写..."
}
```

## LLM

### 一键总结（流式）
```
POST /api/llm/summarize
```

**请求体：**
```json
{
  "audio_file_id": 1,
  "prompt": "总结要求"
}
```

**响应：** Server-Sent Events
```
data: {"token": "这"}
data: {"token": "是"}
data: {"token": "总结"}
data: {"done": true}
```

### 智能问答（流式）
```
POST /api/llm/chat
```

**请求体：**
```json
{
  "project_id": 1,
  "question": "问题内容",
  "history": [
    {"role": "user", "content": "之前的问题"},
    {"role": "assistant", "content": "之前的回答"}
  ]
}
```

**响应：** Server-Sent Events

### 获取聊天历史
```
GET /api/llm/chat/history/{project_id}?limit=50
```

## 系统

### 健康检查
```
GET /health
```

### 系统配置
```
GET /api/config
```

**响应：**
```json
{
  "llm_provider": "ollama",
  "asr_engine": "funasr",
  "max_concurrent": 2,
  "supported_formats": ["wav", "mp3", "m4a", "flac", "ogg"]
}
```

### 音频设备
```
GET /api/audio/devices
```

**响应：**
```json
{
  "devices": [
    {
      "id": 0,
      "name": "Microphone",
      "is_cable": false,
      "channels": 2
    }
  ]
}
```

### 系统统计
```
GET /api/statistics
```

**响应：**
```json
{
  "total_projects": 5,
  "total_audio_files": 20,
  "total_segments": 500,
  "completed_files": 18,
  "failed_files": 1,
  "pending_files": 1,
  "total_duration_hours": 2.5
}
```

### 搜索转写内容
```
GET /api/search?keyword=关键词&limit=10
```

### 转写历史
```
GET /api/history?project_id=1&limit=20
```

## 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 409 | 模型正在运行中 |
| 500 | 服务器内部错误 |