# Changelog

## [1.6.0] - 2026-07-12

### Added
- **系统设置页面重构**
  - 文字模型配置：支持在线修改 provider（llamacpp / aliyun / deepseek）、Base URL、模型名、API Key
  - 多模态模型配置：支持在线修改 provider（dashscope / deepseek / openrouter / custom）、Base URL、模型名、API Key
  - ASR 配置：支持在线修改推理设备（cpu/cuda）、最大并发数（1-8）
  - 并发数 vs 硬件需求对照表（CPU 模式下 4 档配置参考）
  - ASR 模型状态显示：自动检测 ModelScope 缓存是否已有模型文件
  - 所有配置修改即时生效，无需重启服务（`PUT /api/settings` 写入 config.yaml + reload）

### Fixed
- **ASR 模型开箱即用**
  - config.yaml 中 ASR 模型路径留空时，自动使用 ModelScope 默认模型 ID
  - 首次运行自动从 ModelScope 下载 FunASR 模型（总计 ~3.5GB），之后使用本地缓存
  - 修复 config.yaml.example 中 LLM provider 从 `ollama` 更新为 `llamacpp`
- **配置文件同步更新**
  - config.yaml.example 更新为 llamacpp 为默认 provider
  - 多模态配置添加到示例文件

## [1.5.1] - 2026-07-12

### Improved
- **转写内容区域高度优化**
  - 移除 `content-list` 600px 和 `card-content` 300px 的高度限制
  - 转写内容现在充分利用浏览器纵向空间，支持自由滚动
- **发言人名称自定义**
  - 转写内容区域右上角新增「发言人设置」按钮
  - 弹窗支持为每位发言人配置真实姓名
  - 名称持久化到 localStorage，刷新后保留
  - 发言人标签使用彩色圆点区分，PlaybackReview 页面同步生效
- **URL 音视频转写**
  - 音频列表新增「URL」来源选项
  - 支持输入视频/音频链接（YouTube、B站等），自动下载音频并转写
  - 复用 yt-dlp 引擎，仅提取音频部分，转写流程与文件上传一致
  - 后端新增 `POST /api/projects/{id}/download-url` 接口

### Fixed
- `update_segment` 接口参数从 query string 修正为 JSON body，与前端请求格式一致

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
  - 支持 llama.cpp / Aliyun / Deepseek 三种 LLM 提供商
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
