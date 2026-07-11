<div align="center">

<img src="https://img.shields.io/github/stars/sdxwmlyl/Sound2Target?style=social" alt="GitHub Stars">
<img src="https://img.shields.io/github/forks/sdxwmlyl/Sound2Target?style=social" alt="GitHub Forks">

<br/><br/>

# 🎙️ Sound2Target

### *Not to words, just valuable target.*

<br/>

**100% 本地运行的语音转写 + AI 总结系统**

*Record → Transcribe → Summarize → Act. All on your machine. Zero data leaks.*

<br/>

<p>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-2ea44f?style=flat-square" alt="License"></a>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Vue.js-3-4FC08D?style=flat-square&logo=vue.js&logoColor=white" alt="Vue.js">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/100%25_Local-No_Cloud-blueviolet?style=flat-square" alt="Local">
  <img src="https://img.shields.io/github/last-commit/sdxwmlyl/Sound2Target?style=flat-square&color=orange" alt="Last Commit">
</p>

<br/>

**[🇨🇳 中文](#-中文)** · **[🇬🇧 English](#-english)**

<br/>

<!-- TODO: 替换为实际 GIF 演示 — 录制工具: OBS → ezgif.com 转 GIF -->
<!-- ![demo](assets/demo.gif) -->

</div>

---

<a id="-中文"></a>

## 🇨🇳 中文

### 💡 这是什么？

会议开了 2 小时，散会后谁也记不清说了什么。

Sound2Target 把会议录音变成 **可执行的目标** — 不只是一堆文字，而是摘要、观点变化、待办事项。全程本地运行，录音不出你的电脑。

### ⚡ 30 秒上手

```bash
git clone https://github.com/sdxwmlyl/Sound2Target.git
cd Sound2Target/S2T/backend && pip install -r requirements.txt
cp config/config.yaml.example config/config.yaml
cd ../frontend && npm install
cd .. && start.bat
```

> 打开 **http://localhost:3000** → 创建项目 → 上传录音 → 完成 ✅

### 🎯 核心能力

| 能力 | 说明 |
|:-----|:-----|
| 🎤 **多源录音** | 麦克风 / 系统声音(VB-CABLE) / 文件上传 |
| 📝 **智能转写** | FunASR Paraformer-large + 说话人分离 + 热词增强 |
| 🤖 **AI 总结** | 一键摘要 · 智能问答 · 观点演变追踪（流式输出） |
| 🎬 **视频分析** | 输入视频 URL → 自动下载转写 → 截图识别 → 双轨融合总结 |
| 🔌 **Agent 集成** | MCP Server 14 工具 · REST API · 批量流水线 |
| 💻 **低配置友好** | 纯 CPU 可运行，无需独显；8GB 内存即可流畅工作 |
| 🎨 **现代 UI** | Apple 风格 · Markdown 渲染 · 响应式布局 |

> **为什么低配置很重要？** 不是每个人都有 RTX 4090。FunASR 基于 PyTorch CPU 推理，普通笔记本就能跑。LLM 部分通过 llama.cpp 量化模型（Q4_K_M）或云端 API（阿里百炼/Deepseek）解决，显卡门槛为零。

### 🆚 和其他方案的区别

| | Sound2Target | 在线转写服务 | Whisper 本地 |
|:--|:--:|:--:|:--:|
| **数据不出本机** | ✅ | ❌ | ✅ |
| **AI 总结/问答** | ✅ 内置 | ⚠️ 需另接 | ❌ 需自建 |
| **说话人分离** | ✅ | ✅ | ❌ |
| **实时录音转写** | ✅ | ⚠️ | ❌ |
| **观点演变追踪** | ✅ | ❌ | ❌ |
| **视频内容分析** | ✅ URL→总结 | ❌ | ❌ |
| **MCP/Agent 集成** | ✅ 14 工具 | ❌ | ❌ |
| **低配置可运行** | ✅ CPU 即可 | ✅ 云端 | ❌ 需 GPU |
| **中文优化** | ✅ 热词增强 | ⚠️ | ⚠️ |

### 🏗️ 架构

```
┌─────────────────────────────────────────────┐
│            Vue 3 + Element Plus             │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│               FastAPI Backend               │
│  ┌─────────┐ ┌─────────┐ ┌───────────────┐ │
│  │ ASR     │ │ LLM     │ │ 实时录音引擎   │ │
│  │ FunASR  │ │llama.cpp│ │ sounddevice   │ │
│  │Paraformer│ │百炼/DS │ │ WebSocket     │ │
│  └─────────┘ └─────────┘ └───────────────┘ │
│  ┌─────────────────────────────────────────┐│
│  │ 视频分析 │ yt-dlp下载 → 转写 → 截图 →   ││
│  │          │ 多模态识别 → 双轨融合总结     ││
│  └─────────────────────────────────────────┘│
│                  SQLite                     │
└─────────────────────────────────────────────┘
          ▲ MCP Protocol
┌─────────┴───────────────────────────────────┐
│        s2t_mcp_server.py (14 tools)         │
└─────────────────────────────────────────────┘
```

### 📖 使用场景

- **会议记录** — 2 小时会议，5 分钟出摘要
- **访谈转写** — 说话人分离，谁说了什么一目了然
- **课程笔记** — 录音自动转文字 + AI 提炼重点
- **视频内容提取** — 输入 B 站/YouTube 链接，自动转写 + 图表识别 + 结构化总结
- **Agent 工作流** — MCP 工具对接 AI Agent，自动化处理

### 📚 文档

| 文档 | 说明 |
|:-----|:-----|
| [S2T 详细文档](S2T/README.md) | 后端/前端/配置详解 |
| [API 文档](http://localhost:8000/docs) | Swagger UI（启动后访问） |
| [技术设计](docs/technical-design.md) | 架构方案 |
| [需求文档](docs/requirements.md) | 原始需求 |

---

<a id="-english"></a>

## 🇬🇧 English

### 💡 What is it?

A 2-hour meeting ends, and nobody remembers what was decided.

Sound2Target turns recordings into **actionable targets** — not just transcripts, but summaries, viewpoint shifts, and next steps. Runs 100% locally. Your audio never leaves your machine.

### ⚡ Quick Start (30 seconds)

```bash
git clone https://github.com/sdxwmlyl/Sound2Target.git
cd Sound2Target/S2T/backend && pip install -r requirements.txt
cp config/config.yaml.example config/config.yaml
cd ../frontend && npm install
cd .. && start.bat
```

> Open **http://localhost:3000** → Create project → Upload audio → Done ✅

### 🎯 Features

| Capability | Description |
|:-----------|:------------|
| 🎤 **Multi-Source Recording** | Microphone / System audio (VB-CABLE) / File upload |
| 📝 **Smart Transcription** | FunASR Paraformer-large + Speaker diarization + Hotword boost |
| 🤖 **AI Intelligence** | One-click summary · Q&A · Viewpoint evolution tracking |
| 🎬 **Video Analysis** | Input video URL → auto download → transcribe → screenshot → dual-track merge summary |
| 🔌 **Agent Integration** | MCP Server (14 tools) · REST API · Batch pipeline |
| 💻 **Low-Spec Friendly** | Runs on pure CPU, no GPU required; 8GB RAM is enough |
| 🎨 **Modern UI** | Apple-style design · Markdown rendering · Responsive |

> **Why does low-spec matter?** Not everyone has an RTX 4090. FunASR runs on PyTorch CPU inference — any laptop handles it. For LLM, use llama.cpp quantized models (Q4_K_M) or cloud APIs (Aliyun/Deepseek) — zero GPU required.

### 🆚 Why not use X?

| | Sound2Target | Cloud ASR | Whisper Local |
|:--|:--:|:--:|:--:|
| **Data stays local** | ✅ | ❌ | ✅ |
| **Built-in AI summarize** | ✅ | ⚠️ DIY | ❌ |
| **Speaker diarization** | ✅ | ✅ | ❌ |
| **Real-time transcription** | ✅ | ⚠️ | ❌ |
| **Viewpoint tracking** | ✅ | ❌ | ❌ |
| **Video content analysis** | ✅ URL→summary | ❌ | ❌ |
| **MCP/Agent tools** | ✅ 14 tools | ❌ | ❌ |
| **Runs without GPU** | ✅ CPU OK | ✅ Cloud | ❌ Needs GPU |
| **Chinese optimized** | ✅ hotwords | ⚠️ | ⚠️ |

### 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│            Vue 3 + Element Plus             │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│               FastAPI Backend               │
│  ┌─────────┐ ┌─────────┐ ┌───────────────┐ │
│  │ ASR     │ │ LLM     │ │ Realtime      │ │
│  │ FunASR  │ │llama.cpp│ │ sounddevice   │ │
│  └─────────┘ └─────────┘ └───────────────┘ │
│  ┌─────────────────────────────────────────┐│
│  │ Video    │ yt-dlp → transcribe → OCR →  ││
│  │ Analysis │ dual-track merge summary     ││
│  └─────────────────────────────────────────┘│
│                  SQLite                     │
└─────────────────────────────────────────────┘
          ▲ MCP Protocol
┌─────────┴───────────────────────────────────┐
│        s2t_mcp_server.py (14 tools)         │
└─────────────────────────────────────────────┘
```

### 📖 Use Cases

- **Meeting notes** — 2-hour meeting summarized in 5 minutes
- **Interview transcription** — Speaker diarization keeps track of who said what
- **Lecture notes** — Auto-transcribe + AI extracts key points
- **Video content extraction** — Input Bilibili/YouTube link, auto transcribe + chart recognition + structured summary
- **Agent workflows** — MCP tools connect to AI agents for automated processing

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

[MIT](LICENSE)

---

<div align="center">

**Sound2Target** — *Not to words, just valuable target.* 🎯

<br/><br/>

<!-- Star History -->
<a href="https://star-history.com/#sdxwmlyl/Sound2Target&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=sdxwmlyl/Sound2Target&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=sdxwmlyl/Sound2Target&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=sdxwmlyl/Sound2Target&type=Date" width="600" />
 </picture>
</a>

</div>
