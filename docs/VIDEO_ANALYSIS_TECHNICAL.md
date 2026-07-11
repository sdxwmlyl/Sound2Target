# 视频内容分析功能 — 技术设计文档

> 版本: v1.0 | 日期: 2026-07-11

---

## 1. 架构概览

```
用户输入 URL + 总结要求
        │
        ▼
┌─────────────────────────────────────────────┐
│              VideoAnalysis API               │
│  POST /api/video/analyze                    │
└──────────────┬──────────────────────────────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐
│ 音频轨 │ │ 文案轨 │ │ 视觉轨 │
│ yt-dlp │ │ S2T    │ │ 浏览器 │
│ 下载   │ │ 转写   │ │ 截图   │
└───┬────┘ └───┬────┘ └───┬────┘
    │          │          │
    ▼          ▼          ▼
┌─────────────────────────────────────────────┐
│            双轨融合引擎                       │
│  transcript + frames → merged_content       │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│            自定义总结引擎                      │
│  merged_content + user_prompt → summary      │
│  (多模态LLM识别图表 + 文本LLM生成总结)         │
└─────────────────────────────────────────────┘
```

## 2. 模块设计

### 2.1 新增文件

```
S2T/backend/
├── api/
│   └── video.py              # 视频分析 API 端点
├── core/
│   └── video/
│       ├── __init__.py
│       ├── downloader.py     # yt-dlp 音频下载
│       ├── frame_capture.py  # 浏览器帧捕获
│       ├── frame_analyzer.py # 多模态图表识别
│       ├── transcript_filter.py  # 文案关键词筛选
│       └── merger.py         # 双轨融合
├── config/
│   └── settings.py           # 新增 video + multimodal 配置
└── models/
    └── video_analysis.py     # 视频分析任务模型
```

### 2.2 API 设计

#### POST /api/video/analyze

```json
// Request
{
  "url": "https://www.bilibili.com/video/BV13sMi63EAQ/",
  "project_name": "B70评测视频分析",  // 可选，默认从视频标题生成
  "summary_prompt": "提取评测维度、指标和对比思路",
  "sample_interval": 30,  // 可选，默认30秒
  "enable_frame_capture": true,  // 可选，默认true
  "enable_transcript": true,     // 可选，默认true
}

// Response (同步返回，长任务用 SSE)
{
  "project_id": 39,
  "audio_file_id": 67,
  "status": "completed",
  "video_title": "榨干最强蓝厂显卡...",
  "video_duration": 1007.2,
  "transcript_segments": 419,
  "frames_captured": 34,
  "frames_analyzed": 34,
  "content_items": 56,
  "summary": "# 评测方案\n\n## 维度1: ...\n...",
  "merged_content": [...]  // 完整内容清单
}
```

#### GET /api/video/analyze/{task_id}

查询分析任务状态和结果。

### 2.3 核心流程

```python
async def analyze_video(url, summary_prompt, sample_interval):
    # Step 1: 下载音频（~10s）
    audio_path = await download_audio(url)
    
    # Step 2: S2T 转写（~30s）
    project = create_project(video_title)
    audio_file = upload_and_transcribe(project.id, audio_path)
    segments = get_transcript(audio_file.id)
    
    # Step 3: 文案关键词筛选（~1s）
    key_moments = filter_transcript(segments)
    
    # Step 4: 视觉帧捕获（~3min）
    frames = capture_frames(url, sample_interval)
    
    # Step 5: 多模态图表识别（~2min）
    frame_descriptions = analyze_frames(frames)  # 调用多模态LLM
    
    # Step 6: 双轨融合（~1s）
    merged = merge_content(segments, frame_descriptions)
    
    # Step 7: 自定义总结（~30s）
    summary = generate_summary(merged, summary_prompt)
    
    return {
        "project_id": project.id,
        "summary": summary,
        "merged_content": merged
    }
```

### 2.4 视觉帧捕获策略

**双轨合并（不遗漏）**：

| 轨道 | 方法 | 产出 |
|------|------|------|
| A: 文案驱动 | S2T 转写 → 关键词筛选 → 精确帧 | 口述重点 |
| B: 固定间隔 | 每 N 秒截一帧 | 视觉全覆盖 |

**合并逻辑**：
```python
def merge_content(transcript_segments, frame_descriptions):
    # 1. 转写段按时间排序
    # 2. 帧描述按时间排序
    # 3. 15秒窗口内视为同一内容，合并
    # 4. 输出去重后的时间线
    pass
```

### 2.5 多模态图表识别

```python
async def analyze_frame(frame_path, timestamp):
    """调用多模态大模型识别单帧内容"""
    # 将图片编码为 base64
    image_b64 = encode_image(frame_path)
    
    # 调用多模态 API
    response = await call_multimodal_llm(
        prompt="请识别这张图片中的内容。如果是图表/表格，请提取所有数据。",
        image=image_b64
    )
    
    return {
        "timestamp": timestamp,
        "frame_path": frame_path,
        "description": response.text,
        "content_type": classify(response.text)  # chart/table/text/demo
    }
```

### 2.6 自定义总结

```python
async def generate_summary(merged_content, user_prompt):
    """调用文本 LLM 生成自定义总结"""
    
    # 构建 prompt
    system_prompt = f"""你是一位专业的内容分析师。
用户要求：{user_prompt}

请基于以下完整内容清单，按用户要求生成结构化总结。
内容清单包含时间戳、文案内容、视觉帧描述。"""

    content_text = format_merged_content(merged_content)
    
    response = await call_text_llm(
        system=system_prompt,
        user=content_text
    )
    
    return response.text
```

## 3. 数据模型

### video_analysis_tasks 表

```sql
CREATE TABLE video_analysis_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    url TEXT NOT NULL,
    video_title TEXT,
    video_duration REAL,
    summary_prompt TEXT,
    sample_interval INTEGER DEFAULT 30,
    status TEXT DEFAULT 'pending',  -- pending/downloading/transcribing/capturing/analyzing/completed/failed
    audio_file_id INTEGER,
    transcript_segments INTEGER DEFAULT 0,
    frames_captured INTEGER DEFAULT 0,
    frames_analyzed INTEGER DEFAULT 0,
    content_items INTEGER DEFAULT 0,
    summary TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 4. 配置扩展

### config.yaml 新增

```yaml
# 视频分析配置
video:
  yt_dlp_path: "yt-dlp"
  sample_interval: 30        # 默认采样间隔（秒）
  max_duration: 3600         # 最大视频时长（秒）
  browser_timeout: 300       # 浏览器超时（秒）
  temp_dir: "./data/video_temp"  # 临时文件目录

# 多模态大模型配置（用于图表识别）
multimodal:
  provider: "dashscope"      # dashscope / openai / ollama
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  model: "qwen-vl-max"
  api_key: ""               # 也可通过环境变量 MULTIMODAL_API_KEY 设置
  max_tokens: 2048
```

## 5. 技术选型

| 组件 | 选择 | 理由 |
|------|------|------|
| 视频下载 | yt-dlp | 支持 Bilibili/YouTube 等所有主流平台 |
| 音频转写 | FunASR（现有） | 复用，零额外开发 |
| 帧捕获 | Playwright（现有） | 复用浏览器环境，支持 JS 渲染的页面 |
| 图表识别 | 多模态大模型 API | 需要视觉理解能力，本地模型精度不足 |
| 文案筛选 | 关键词匹配 | 简单高效，可配置 |
| 融合分析 | 时间窗口对齐 | 15秒窗口足够覆盖口述-画面的时间差 |
| 自定义总结 | 文本 LLM（现有） | 复用 ollama/aliyun/deepseek 配置 |
| 任务管理 | SQLite（现有） | 复用现有数据库 |

## 6. 风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| Bilibili 反爬 | 音频下载失败 | 使用登录 Cookie；支持手动上传音频作为 fallback |
| 多模态 API 不可用 | 图表识别跳过 | 降级为纯文案分析；提示用户配置 API |
| 视频过长 | 处理超时 | 限制最大时长（默认 1 小时）；支持分段处理 |
| 浏览器环境不可用 | 帧捕获失败 | 降级为纯文案分析；提示用户启动浏览器 |
