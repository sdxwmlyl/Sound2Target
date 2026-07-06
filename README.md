# 🎙️ Sound2Target (S2T) — 本地化语音转写系统

> 100% 本地运行的会议录音、实时转写、AI 总结一站式解决方案。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3-brightgreen.svg)](https://vuejs.org/)

---

## ✨ 功能特性

| 模块 | 能力 |
|------|------|
| 🎤 **多源录音** | 麦克风录音、系统声音捕获（VB-CABLE）、文件上传（wav/mp3/m4a/flac/ogg） |
| 📝 **智能转写** | FunASR Paraformer-large 语音识别 + CAMP++ 说话人分离 + 热词增强 |
| 🤖 **AI 能力** | 一键总结（流式输出）、智能问答、观点提取与演变追踪 |
| 📁 **项目管理** | 项目-音频文件层级、转写结果编辑、历史记录、全文搜索 |
| 🎨 **现代 UI** | Apple 风格设计、Markdown 渲染、响应式布局 |
| 🔌 **MCP Server** | 12 个 MCP 工具，支持 AI Agent 集成调用 |

## 🏗️ 技术架构

```
Sound2Target/
├── S2T/
│   ├── backend/           # FastAPI 后端
│   │   ├── api/           # REST API 路由
│   │   ├── core/          # 核心模块（ASR、LLM、音频捕获）
│   │   ├── config/        # 配置文件
│   │   ├── models/        # 数据模型（SQLite）
│   │   └── utils/         # 工具函数
│   ├── frontend/          # Vue 3 + Element Plus 前端
│   ├── tests/             # 测试用例
│   └── docs/              # 项目文档
├── s2t_mcp_server.py      # MCP Server（AI Agent 集成）
├── pipeline.py            # 批量转写流水线
└── start_bg_recording.py  # 后台录音脚本
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- （可选）CUDA GPU — 加速 ASR 推理
- （可选）Ollama — 本地 LLM 推理

### 安装

```bash
# 克隆仓库
git clone https://github.com/sdxwmlyl/Sound2Target.git
cd Sound2Target

# 后端依赖
cd S2T/backend
pip install -r requirements.txt

# 前端依赖
cd ../frontend
npm install
```

### 配置

```bash
# 复制配置模板
cp S2T/backend/config/config.yaml.example S2T/backend/config/config.yaml

# 编辑配置，指定 ASR 模型路径和 LLM provider
```

#### LLM 环境变量（按需设置）

```bash
# 阿里百炼
export ALIYUN_API_KEY=your_api_key

# Deepseek
export DEEPSEEK_API_KEY=your_api_key
```

### 启动

```bash
# 方式一：一键启动
cd S2T
./start.bat

# 方式二：分别启动
# 终端 1 - 后端
cd S2T/backend
python -m uvicorn main:app --host localhost --port 8000

# 终端 2 - 前端
cd S2T/frontend
npm run dev
```

访问 http://localhost:3000 🎉

### 系统声音录制（可选）

1. 安装 [VB-Audio Virtual Cable](https://vb-audio.com/Cable/)
2. Windows 声音设置 → 输出设备选择 **"CABLE Input"**
3. 在 S2T 中选择"系统"录音模式

## 📖 使用流程

```
创建项目 → 上传音频/开始录音 → 自动转写 → AI 总结/问答
                                        ↓
                                  观点提取与演变追踪
```

### MCP Server（AI Agent 集成）

```bash
# 启动 MCP Server
python s2t_mcp_server.py
```

提供 12 个工具：`create_project`、`start_system_recording`、`stop_recording`、`get_transcript_text`、`summarize_project`、`extract_viewpoints` 等。

## 🔧 ASR 配置说明

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `speech_noise_threshold` | VAD 噪声阈值 | 0.5（默认 0.8 过高） |
| `max_concurrent` | 并发转写数 | 2（CPU）/ 4（GPU） |
| `device` | 推理设备 | `cpu` / `cuda` |

### 热词配置

在录音时输入热词（空格分隔），可提高专业术语识别率：

```
人工智能 机器学习 深度学习 大语言模型
```

## 📚 文档

- [需求文档](docs/requirements.md)
- [技术设计](docs/technical-design.md)
- [S2T 详细文档](S2T/README.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

[MIT License](LICENSE) — 自由使用、修改和分发。

---

> **Sound2Target** — 把声音变成目标。🎯
