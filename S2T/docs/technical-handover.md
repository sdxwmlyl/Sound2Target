# S2T 语音转写系统 - 技术交接文档

## 一、项目背景

整合三个已有项目，构建统一的本地语音转写系统：

| 原项目 | 核心能力 |
|--------|----------|
| ProjectLocalASR | 批量文件转写、任务队列 |
| ProjectRec2Sum | 发言人分离、AI总结 |
| ProjectSound2Answer | 实时音频捕获、WebSocket |

## 二、技术选型（已验证）

| 模块 | 选择 | 原因 |
|------|------|------|
| 后端 | FastAPI | 异步支持好，WebSocket原生支持 |
| 前端 | Vue 3 + Element Plus | 国内生态好，组件丰富 |
| 数据库 | SQLite | 轻量零配置，适合本地项目 |
| ASR | FunASR (Paraformer + CAMP++) | 发言人分离成熟 |
| LLM | Ollama / 阿里百炼 / Deepseek | 本地+在线双模式 |
| 音频 | sounddevice + WebSocket | 实时捕获 |

## 三、核心架构

```
S2T/
├── backend/
│   ├── main.py              # FastAPI入口
│   ├── config/config.yaml   # 配置文件
│   ├── core/
│   │   ├── asr/engine.py    # ASR引擎封装
│   │   ├── llm/ollama.py    # LLM接口
│   │   ├── audio/capture.py # 音频捕获
│   │   ├── realtime.py      # 实时录音管理
│   │   └── model_state.py   # 模型互斥状态
│   ├── api/                 # REST API路由
│   └── models/              # SQLite数据模型
├── frontend/src/
│   ├── views/               # 页面组件
│   ├── components/          # 通用组件
│   └── api/index.js         # API封装
└── data/                    # 数据存储
```

## 四、关键设计决策

### 4.1 数据模型（取消会话层级）
```
Project (项目)
  ├── hotwords (热词，空格分隔)
  └── AudioFile (音频文件)
        ├── source_type: file/microphone/system
        ├── status: pending/processing/completed/failed
        ├── summary: AI总结内容
        └── TranscriptSegment (转写段落)
```

### 4.2 模型互斥（重要）
ASR和LLM不能同时运行（显存限制），需要状态管理：

```python
# core/model_state.py
class ModelState:
    _asr_running = False
    _llm_running = False
    
    async def acquire_asr(self) -> bool:
        if self._llm_running:
            return False  # LLM运行中，ASR不能启动
        self._asr_running = True
        return True
```

### 4.3 实时录音流程
1. 前端WebSocket连接
2. 音频数据写入WAV文件（不实时转写）
3. 录音停止后，后台异步转写
4. 转写完成更新数据库状态

### 4.4 热词格式
FunASR热词用**空格分隔**，不是逗号：
```python
hotword = "人工智能 机器学习 深度学习"
model.generate(input=audio, hotword=hotword)
```

### 4.5 系统声音捕获
需要VB-Audio Virtual Cable：
1. 安装CABLE驱动
2. Windows声音设置 → 输出选择 "CABLE Input"
3. 使用sounddevice捕获CABLE Output设备
4. 多声道混音为单声道

### 4.6 流式输出
LLM使用Server-Sent Events (SSE)流式返回：
```python
async def generate():
    async for token in llm.generate_stream(prompt):
        yield f"data: {json.dumps({'token': token})}\n\n"
    yield f"data: {json.dumps({'done': True})}\n\n"

return StreamingResponse(generate(), media_type="text/event-stream")
```

## 五、已踩坑点

| 问题 | 解决方案 |
|------|----------|
| Pinia解构丢失响应性 | 使用`storeToRefs` |
| 热词不生效 | 格式改为空格分隔 |
| 系统录音无声 | 设置CABLE为默认播放设备 |
| 转写阻塞前端 | 改为后台异步任务 |
| ASR/LLM同时运行OOM | 添加ModelState互斥 |
| WebSocket关闭警告 | 异常处理改为debug级别 |
| 多声道设备只取1声道 | 改为全部声道混音 |

## 六、配置文件示例

```yaml
# backend/config/config.yaml
asr:
  engine: funasr
  model: C:/Users/xxx/.cache/modelscope/hub/models/iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch
  spk_model: C:/Users/xxx/.cache/modelscope/hub/models/iic/speech_campplus_sv_zh-cn_16k-common
  vad_model: C:/Users/xxx/.cache/modelscope/hub/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch
  punc_model: C:/Users/xxx/.cache/modelscope/hub/models/iic/punc_ct-transformer_cn-en-common-vocab471067-large
  max_concurrent: 2
  device: cuda

llm:
  provider: ollama
  ollama:
    base_url: http://localhost:11434
    model: qwen3.5:9b

audio:
  sample_rate: 16000
  chunk_duration: 0.5
  supported_formats: [wav, mp3, m4a, flac, ogg]
```

## 七、启动方式

```bash
# 后端
cd S2T/backend
pip install -r requirements.txt
python -m uvicorn main:app --host localhost --port 8000

# 前端
cd S2T/frontend
npm install
npm run dev
```

## 八、API路由清单

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/projects | 项目列表 |
| POST | /api/projects | 创建项目 |
| GET | /api/projects/{id} | 项目详情 |
| PUT | /api/projects/{id}/hotwords | 更新热词 |
| GET | /api/projects/{id}/audio-files | 音频列表 |
| POST | /api/projects/{id}/upload | 上传音频 |
| GET | /api/audio-files/{id}/transcript | 转写结果 |
| POST | /api/llm/summarize | 一键总结(SSE) |
| POST | /api/llm/chat | 智能问答(SSE) |
| WS | /api/realtime/ws/{project_id} | 实时录音 |

## 九、依赖清单

**后端：**
```
fastapi, uvicorn, pydantic, pyyaml, aiofiles
funasr, torch, torchaudio
pydub, sounddevice, soundfile, numpy
aiohttp
```

**前端：**
```
vue@3, vue-router@4, pinia
element-plus, @element-plus/icons-vue
axios, marked
```

## 十、测试验证

```bash
# 后端测试
cd S2T/tests
pytest test_models.py -v

# API测试
curl http://localhost:8000/health
curl http://localhost:8000/api/projects
```