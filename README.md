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

**[🇨🇳 中文](README.md)** · **[🇬🇧 English](README.en.md)**

<br/>

<!-- TODO: 替换为实际 GIF 演示 — 录制工具: OBS → ezgif.com 转 GIF -->
<!-- ![demo](assets/demo.gif) -->

</div>

---

## 💡 这是什么？

会议开了 2 小时，散会后谁也记不清说了什么。

Sound2Target 把会议录音变成 **可执行的目标** — 不只是一堆文字，而是摘要、观点变化、待办事项。全程本地运行，录音不出你的电脑。

### 🎬 典型场景

Sound2Target 支持四种音频输入方式，覆盖从线上到线下的全部会议场景：

| 场景 | 音频源 | 怎么用 |
|:-----|:-------|:-------|
| **📺 B 站/YouTube 视频总结** | URL | 粘贴视频链接 → 自动下载音频 → 转写 → AI 总结。适合技术分享、产品评测、课程回放等需要快速提炼要点的场景。 |
| **💻 腾讯会议在线识别** | 系统声音 | 通过 VB-CABLE 捕获系统内声音，会议进行中实时转写。适合线上参会时，同步获取文字记录和 AI 摘要。 |
| **🏢 现场会议录音** | 麦克风 | 用任意一台电脑的麦克风收音，实时转写 + 说话人分离。适合线下会议室、头脑风暴、客户拜访等现场场景。 |
| **📱 手机录音导入** | 文件上传 | 将手机录音（mp3/m4a/wav/flac/ogg）上传至项目，自动转写 + AI 总结。适合事后整理电话会议、外出录音等离线素材。 |

> 四种方式可以混用在同一个项目中 — 比如一场混合会议，线上部分用系统声音录，线下部分用麦克风录，最后合并到同一个项目里统一总结。

## ⚡ 30 秒上手

```bash
git clone https://github.com/sdxwmlyl/Sound2Target.git
cd Sound2Target/S2T/backend && pip install -r requirements.txt
cp config/config.yaml.example config/config.yaml
cd ../frontend && npm install
cd .. && start.bat
```

> 打开 **http://localhost:3000** → 创建项目 → 上传录音 → 完成 ✅

## 🎯 核心能力

| 能力 | 说明 |
|:-----|:-----|
| 🎤 **多源录音** | 麦克风 / 系统声音(VB-CABLE) / 文件上传 / URL 下载 |
| 📝 **智能转写** | FunASR Paraformer-large + 说话人分离 + 热词增强 |
| 🤖 **AI 总结** | 一键摘要 · 智能问答 · 观点演变追踪 · 自定义发言人名称（流式输出） |
| 🎬 **视频分析** | 输入视频 URL → 自动下载转写 → 截图识别 → 双轨融合总结 |
| 🔌 **Agent 集成** | MCP Server 14 工具 · REST API · 批量流水线 |
| 💻 **低配置友好** | 纯 CPU 可运行，无需独显；8GB 内存即可流畅工作 |
| 🎨 **现代 UI** | Apple 风格 · Markdown 渲染 · 响应式布局 |

> **为什么低配置很重要？** 不是每个人都有 RTX 4090。FunASR 基于 PyTorch CPU 推理，普通笔记本就能跑。LLM 部分通过 llama.cpp 量化模型（Q4_K_M）或云端 API（阿里百炼/Deepseek）解决，显卡门槛为零。

## 🆚 和其他方案的区别

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

## 🏗️ 架构

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

## 📋 版本日志

| 版本 | 日期 | 亮点 |
|:-----|:-----|:-----|
| **v1.5.1** | 2026-07-12 | 🖥️ 转写区域高度优化 · 🏷️ 发言人名称自定义（持久化+同步至AI） · 🔗 URL 音视频转写入口 |
| **v1.5.0** | 2026-07-11 | 🎬 视频内容分析（URL→转写→截图→多模态识别→融合总结）· LLM 引擎统一为 llama.cpp · MCP 14 工具 |
| **v1.4.0** | 2026-06-21 | 🔍 观点演变提取（三阶段处理+逻辑链+矛盾检测）|
| **v1.3.0** | 2026-06-15 | 🤖 AI 总结功能（Ollama/百炼/Deepseek 三引擎）|
| **v1.2.0** | 2026-06-01 | 📁 文件上传转写 · MCP 工具扩展 |
| **v1.1.0** | 2026-05-15 | 🎙️ 实时录音转写 · WebSocket 音频流 |
| **v1.0.0** | 2026-05-01 | 🎉 首发：项目管理 · 基础转写 · FunASR 引擎 |

## 📚 文档

| 文档 | 说明 |
|:-----|:-----|
| [S2T 详细文档](S2T/README.md) | 后端/前端/配置详解 |
| [API 文档](http://localhost:8000/docs) | Swagger UI（启动后访问） |
| [技术设计](docs/technical-design.md) | 架构方案 |
| [需求文档](docs/requirements.md) | 原始需求 |

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
