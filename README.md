<div align="center">

# 🎙️ Sound2Target

### *Not to words, just valuable target.*

<p>
  <strong>本地化语音转写 · AI 总结 · 观点追踪</strong><br/>
  <em>Local-first speech transcription · AI summarization · viewpoint tracking</em>
</p>

<p>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-2ea44f?style=flat-square" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Vue.js-3-4FC08D?style=flat-square&logo=vue.js&logoColor=white" alt="Vue.js">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/100%25_Local-No_Cloud_Required-blueviolet?style=flat-square" alt="100% Local">
</p>

<br/>

<p>
  <b>中文</b> | <a href="#english">English</a>
</p>

</div>

---

## 🇨🇳 中文

### 一句话介绍

> 把会议录音变成**可操作的目标**，而不是一堆文字。
> 录音 → 转写 → AI 总结 → 观点演变追踪，全程本地运行，零数据外泄。

### ✨ 核心能力

<table>
<tr>
<td width="50%">

#### 🎤 多源录音
- 麦克风实时录音
- 系统声音捕获（VB-CABLE）
- 文件上传（wav/mp3/m4a/flac/ogg）
- 后台静默录音，不干扰工作

</td>
<td width="50%">

#### 📝 智能转写
- FunASR Paraformer-large 语音识别
- CAMP++ 说话人分离
- 热词增强（专业术语识别率 ↑）
- 批量并发转写

</td>
</tr>
<tr>
<td>

#### 🤖 AI 能力
- 一键总结（流式输出）
- 智能问答（基于转写内容）
- 观点提取与演变追踪
- 多 LLM 支持：Ollama / 阿里百炼 / Deepseek

</td>
<td>

#### 🔌 Agent 集成
- MCP Server（12 个工具）
- 支持 AI Agent 调用
- 批量转写流水线
- 标准 REST API

</td>
</tr>
</table>

### 🏗️ 技术架构

```
┌─────────────────────────────────────────────────┐
│                   Vue 3 Frontend                │
│          Element Plus · Apple 风格 UI           │
└──────────────────────┬──────────────────────────┘
                       │ HTTP / WebSocket
┌──────────────────────▼──────────────────────────┐
│                  FastAPI Backend                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ ASR 引擎  │ │ LLM 引擎  │ │   实时录音引擎    │ │
│  │FunASR    │ │Ollama    │ │sounddevice      │ │
│  │Paraformer│ │百炼/DS   │ │WebSocket        │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
│                    SQLite                        │
└─────────────────────────────────────────────────┘
          ▲
          │ MCP Protocol
┌─────────┴───────────────────────────────────────┐
│              s2t_mcp_server.py                   │
│         AI Agent 集成 · 12 工具                  │
└─────────────────────────────────────────────────┘
```

### 🚀 快速开始

```bash
# 1. 克隆
git clone https://github.com/sdxwmlyl/Sound2Target.git
cd Sound2Target

# 2. 后端
cd S2T/backend
pip install -r requirements.txt
cp config/config.yaml.example config/config.yaml
# 编辑 config.yaml，配置 ASR 模型路径和 LLM provider

# 3. 前端
cd ../frontend
npm install

# 4. 启动
cd ..
start.bat   # 一键启动前后端
```

> 浏览器访问 **http://localhost:3000** 🎉

#### 系统声音录制（可选）

1. 安装 [VB-Audio Virtual Cable](https://vb-audio.com/Cable/)
2. Windows 声音设置 → 输出设备选择 **"CABLE Input"**
3. S2T 中选择"系统"录音模式

### 📖 使用流程

```
创建项目 → 上传音频 / 开始录音 → 自动转写 → AI 总结 / 智能问答
                                            ↓
                                    观点提取与演变追踪
```

### 📚 文档

| 文档 | 说明 |
|------|------|
| [S2T 详细文档](S2T/README.md) | 后端/前端/配置详解 |
| [需求文档](docs/requirements.md) | 原始需求设计 |
| [技术设计](docs/technical-design.md) | 技术方案 |
| [API 文档](http://localhost:8000/docs) | 启动后端后访问 |

---

<a id="english"></a>

## 🇬🇧 English

### One-liner

> Turn meeting recordings into **actionable targets**, not just words.
> Record → Transcribe → AI Summarize → Track viewpoint evolution — all locally, zero data leaks.

### ✨ Features

<table>
<tr>
<td width="50%">

#### 🎤 Multi-Source Recording
- Real-time microphone capture
- System audio capture (VB-CABLE)
- File upload (wav/mp3/m4a/flac/ogg)
- Background silent recording

</td>
<td width="50%">

#### 📝 Smart Transcription
- FunASR Paraformer-large ASR
- CAMP++ speaker diarization
- Hotword boosting for domain terms
- Batch concurrent transcription

</td>
</tr>
<tr>
<td>

#### 🤖 AI Capabilities
- One-click summarization (streaming)
- Q&A over transcription
- Viewpoint extraction & evolution tracking
- Multi-LLM: Ollama / Aliyun / Deepseek

</td>
<td>

#### 🔌 Agent Integration
- MCP Server (12 tools)
- AI Agent compatible
- Batch transcription pipeline
- Standard REST API

</td>
</tr>
</table>

### 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/sdxwmlyl/Sound2Target.git
cd Sound2Target

# 2. Backend
cd S2T/backend
pip install -r requirements.txt
cp config/config.yaml.example config/config.yaml
# Edit config.yaml — set ASR model path and LLM provider

# 3. Frontend
cd ../frontend
npm install

# 4. Launch
cd ..
start.bat   # Start both backend & frontend
```

> Open **http://localhost:3000** in your browser 🎉

### 🧩 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + SQLite |
| Frontend | Vue 3 + Element Plus |
| ASR | FunASR (Paraformer + CAMP++) |
| LLM | Ollama / Aliyun Bailian / Deepseek |
| Audio | sounddevice + WebSocket |
| Agent | MCP Protocol (12 tools) |

---

## 🤝 Contributing

Issues and pull requests are welcome!

## 📄 License

[MIT](LICENSE) — use it, fork it, ship it.

---

<div align="center">

**Sound2Target** — *Not to words, just valuable target.* 🎯

</div>
