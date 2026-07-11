# Changelog

## [1.5.0] - 2026-07-11

### Added
- **视频内容分析功能** (`api/video.py`)
  - 输入视频 URL → 自动完成：下载音频 → 转写 → 截图 → 多模态识别 → 融合总结
  - 支持用户自定义总结要求（如"提取评测维度"、"列出所有数据表格"）
  - 双轨合并策略：文案驱动 + 视觉全量扫描，确保不遗漏任何内容
  - 多模态大模型图表识别（需配置 `multimodal` 配置项）
- **新增配置项**
  - `video.*` — 视频分析配置（yt-dlp路径、采样间隔、最大时长等）
  - `multimodal.*` — 多模态大模型配置（provider、base_url、model、api_key）
- **新增 MCP 工具**
  - `analyze_video` — 视频内容分析（URL + 自定义总结要求）
- **新增文档**
  - `docs/VIDEO_ANALYSIS_REQUIREMENTS.md` — 需求文档
  - `docs/VIDEO_ANALYSIS_TECHNICAL.md` — 技术设计文档

### Dependencies
- yt-dlp >= 2026.7 (新增)
- Playwright (已有)
- FunASR (已有)
- 多模态大模型 API (需配置)

## [1.4.0] - 2026-06-21

### Added
- 观点演变提取功能 (`api/viewpoint.py`)
  - 三阶段处理：逐块提取 → 合并分析 → 格式化报告
  - 追踪观点演变 + 逻辑链 + 矛盾检测
  - SSE 流式返回（前端用）+ 同步返回（MCP 用）
- MCP 工具 `extract_viewpoints`

## [1.3.0] - 2026-06-15

### Added
- AI 总结功能 (`api/llm.py`)
  - 支持 Ollama / Aliyun / Deepseek 三种 LLM 提供商
  - 流式总结 + 逐块处理长文本
- MCP 工具 `summarize_project`

## [1.2.0] - 2026-06-01

### Added
- 文件上传转写 (`api/transcribe.py`)
  - 支持 wav/mp3/m4a/flac/ogg 格式
  - 自动触发后台转写
- MCP 工具 `check_audio_file_status` / `get_transcript_text`

## [1.1.0] - 2026-05-15

### Added
- 实时录音转写 (`api/realtime.py`)
- WebSocket 音频流 (`api/audio.py`)
- MCP 工具 `start_system_recording` / `stop_recording`

## [1.0.0] - 2026-05-01

### Added
- 初始版本
- 项目管理 (`api/projects.py`)
- 基础转写功能
- FunASR ASR 引擎
