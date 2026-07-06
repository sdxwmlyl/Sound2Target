# S2T - 语音转写系统

本地化语音转写解决方案，支持离线闭环运行。

## 功能特性

### 核心功能
- **多源音频支持**
  - 文件上传（wav, mp3, m4a, flac, ogg）
  - 麦克风实时录音
  - 系统内置声音捕获（需CABLE虚拟音频设备）

- **智能转写**
  - FunASR Paraformer-large 语音识别
  - CAMP++ 发言人分离
  - 热词配置（提高专业术语识别率）
  - 批量并发转写

- **AI能力**
  - 一键总结（流式输出）
  - 智能问答（流式输出）
  - 支持Ollama/阿里百炼/Deepseek

- **项目管理**
  - 项目-音频文件层级结构
  - 转写结果编辑
  - 历史记录查询
  - 内容搜索

### UI特性
- 苹果现代风格设计
- Markdown渲染
- 响应式布局

## 快速启动

### 方式一：一键启动
```bash
双击 S2T\start.bat
```

### 方式二：分别启动

**后端：**
```bash
cd S2T/backend
pip install -r requirements.txt
python -m uvicorn main:app --host localhost --port 8000
```

**前端：**
```bash
cd S2T/frontend
npm install
npm run dev
```

访问 http://localhost:3000

## 系统配置

### 环境变量
```bash
# 阿里百炼API密钥
export ALIYUN_API_KEY=your_api_key

# Deepseek API密钥
export DEEPSEEK_API_KEY=your_api_key
```

### 配置文件
编辑 `S2T/backend/config/config.yaml`：

```yaml
asr:
  engine: funasr
  model: /path/to/model  # 本地模型路径
  max_concurrent: 2
  device: cuda

llm:
  provider: ollama  # ollama / aliyun / deepseek
  ollama:
    base_url: http://localhost:11434
    model: qwen3.5:9b
```

### 系统声音录制
1. 安装 [VB-Audio Virtual Cable](https://vb-audio.com/Cable/)
2. Windows声音设置 → 输出设备选择 "CABLE Input"
3. 在应用中选择"系统"录音

## 目录结构

```
S2T/
├── backend/
│   ├── main.py              # FastAPI入口
│   ├── config/              # 配置文件
│   ├── core/                # 核心模块
│   │   ├── asr/             # ASR引擎
│   │   ├── llm/             # LLM接口
│   │   ├── audio/           # 音频捕获
│   │   ├── realtime.py      # 实时录音
│   │   └── model_state.py   # 模型状态管理
│   ├── api/                 # API路由
│   ├── models/              # 数据模型
│   └── utils/               # 工具函数
├── frontend/
│   └── src/
│       ├── views/           # 页面组件
│       ├── components/      # 通用组件
│       ├── api/             # API调用
│       └── stores/          # 状态管理
├── data/                    # 数据存储
├── docs/                    # 文档
├── start.bat                # 启动脚本
└── README.md
```

## 技术栈

| 模块 | 技术 |
|------|------|
| 后端 | FastAPI + SQLite |
| 前端 | Vue 3 + Element Plus |
| ASR | FunASR (Paraformer + CAMP++) |
| LLM | Ollama / 阿里百炼 / Deepseek |
| 音频 | sounddevice + WebSocket |

## 模型依赖

### ASR模型（自动下载）
- speech_paraformer-large-vad-punc
- speech_fsmn_vad
- punc_ct-transformer
- speech_campplus_sv

### LLM模型（需预先安装）
```bash
# Ollama
ollama pull qwen3.5:9b
```

## API文档

启动后端后访问：http://localhost:8000/docs

## 常见问题

### Q: 热词不生效？
A: 热词用空格分隔，如：`人工智能 机器学习`

### Q: 系统录音无声？
A: 需要在Windows声音设置中将输出设备改为 "CABLE Input"

### Q: 转写很慢？
A: ASR和LLM不能同时运行，会自动排队

## 开发说明

### 运行测试
```bash
cd S2T/tests
pytest test_models.py -v
```

### 项目文档
- 原始需求：`docs/requirements.md`
- 技术设计：`docs/technical-design.md`

## 许可证

MIT License