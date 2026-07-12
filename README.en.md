<div align="center">

<img src="https://img.shields.io/github/stars/sdxwmlyl/Sound2Target?style=social" alt="GitHub Stars">
<img src="https://img.shields.io/github/forks/sdxwmlyl/Sound2Target?style=social" alt="GitHub Forks">

<br/><br/>

# 🎙️ Sound2Target

### *Not to words, just valuable target.*

<br/>

**100% local speech transcription + AI summarization system**

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

**[🇨🇳 中文](README.md)** · **[🇬🇧 English](README.en.md)**

<br/>

<!-- TODO: Replace with actual GIF demo — Record with OBS → convert at ezgif.com -->
<!-- ![demo](assets/demo.gif) -->

</div>

---

## 💡 What is it?

A 2-hour meeting ends, and nobody remembers what was decided.

Sound2Target turns recordings into **actionable targets** — not just transcripts, but summaries, viewpoint shifts, and next steps. Runs 100% locally. Your audio never leaves your machine.

### 🎬 Typical Scenarios

Sound2Target supports four audio input methods, covering every meeting scenario from online to on-site:

| Scenario | Audio Source | How to Use |
|:---------|:-------------|:-----------|
| **📺 Bilibili / YouTube Summary** | URL | Paste a video link → auto download audio → transcribe → AI summarize. Perfect for tech talks, product reviews, course replays — quickly extract key points from any video. |
| **💻 Tencent Meeting Live Transcription** | System Audio | Capture in-system audio via VB-CABLE for real-time transcription during online meetings. Get live text and AI summaries as the meeting happens. |
| **🏢 On-site Meeting Recording** | Microphone | Use any computer's microphone to capture room audio in real-time with speaker diarization. Ideal for in-person meetings, brainstorming sessions, and client visits. |
| **📱 Phone Recording Import** | File Upload | Upload phone recordings (mp3/m4a/wav/flac/ogg) to a project for auto-transcription and AI summarization. Great for post-hoc processing of phone calls and field recordings. |

> All four methods can be mixed within the same project — for example, in a hybrid meeting, record the online portion via system audio and the in-room portion via microphone, then merge everything into one unified summary.

## ⚡ Quick Start (30 seconds)

```bash
git clone https://github.com/sdxwmlyl/Sound2Target.git
cd Sound2Target/S2T/backend && pip install -r requirements.txt
cp config/config.yaml.example config/config.yaml
cd ../frontend && npm install
cd .. && start.bat
```

> Open **http://localhost:3000** → Create project → Upload audio → Done ✅

## 🎯 Features

| Capability | Description |
|:-----------|:------------|
| 🎤 **Multi-Source Recording** | Microphone / System audio (VB-CABLE) / File upload / URL download |
| 📝 **Smart Transcription** | FunASR Paraformer-large + Speaker diarization + Hotword boost |
| 🤖 **AI Intelligence** | One-click summary · Q&A · Viewpoint evolution tracking · Custom speaker names (streaming) |
| 🎬 **Video Analysis** | Input video URL → auto download → transcribe → screenshot → dual-track merge summary |
| 🔌 **Agent Integration** | MCP Server (14 tools) · REST API · Batch pipeline |
| 💻 **Low-Spec Friendly** | Runs on pure CPU, no GPU required; 8GB RAM is enough |
| 🎨 **Modern UI** | Apple-style design · Markdown rendering · Responsive |

> **Why does low-spec matter?** Not everyone has an RTX 4090. FunASR runs on PyTorch CPU inference — any laptop handles it. For LLM, use llama.cpp quantized models (Q4_K_M) or cloud APIs (Aliyun/Deepseek) — zero GPU required.

## 🆚 Why not use X?

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

## 🏗️ Architecture

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
│  │Paraformer│ │Aliyun/DS│ │ WebSocket     │ │
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

## 📋 Changelog

| Version | Date | Highlights |
|:--------|:-----|:-----------|
| **v1.5.1** | 2026-07-12 | 🖥️ Transcript area height fix · 🏷️ Custom speaker names (persisted + synced to AI) · 🔗 URL audio/video transcription entry |
| **v1.5.0** | 2026-07-11 | 🎬 Video content analysis (URL→transcribe→screenshot→multimodal→merge summary) · LLM unified to llama.cpp · MCP 14 tools |
| **v1.4.0** | 2026-06-21 | 🔍 Viewpoint evolution extraction (3-phase pipeline + logic chains + contradiction detection) |
| **v1.3.0** | 2026-06-15 | 🤖 AI summarization (Ollama / Aliyun / Deepseek triple engine) |
| **v1.2.0** | 2026-06-01 | 📁 File upload transcription · MCP tool expansion |
| **v1.1.0** | 2026-05-15 | 🎙️ Real-time recording transcription · WebSocket audio stream |
| **v1.0.0** | 2026-05-01 | 🎉 Initial release: project management · basic transcription · FunASR engine |

## 📚 Documentation

| Document | Description |
|:---------|:------------|
| [S2T Detailed Docs](S2T/README.md) | Backend / Frontend / Configuration |
| [API Docs](http://localhost:8000/docs) | Swagger UI (available after startup) |
| [Technical Design](docs/technical-design.md) | Architecture |
| [Requirements](docs/requirements.md) | Original requirements |

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
