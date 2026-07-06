# 技术设计文档 (v2)

## 1. 架构决策

### 1.1 整体架构
- **方案**: 模块化单体架构
- **前端**: Vue 3 + Vite + Element Plus
- **后端**: FastAPI
- **数据库**: SQLite

### 1.2 设计原则
- 本地离线优先
- 模块边界清晰，后续可拆分为微服务
- 复用现有模型文件
- 苹果现代风格UI设计

## 2. 技术选型

### 2.1 ASR引擎
- **选择**: FunASR统一方案
- **模型**: Paraformer-large + CAMP++ (发言人分离)
- **热词**: 支持手动配置

### 2.2 LLM集成
- **本地**: Ollama (qwen2.5:7b / qwen3:8b)
- **在线**: 阿里百炼、Deepseek (OpenAI兼容格式)
- **用途**: 转写结果总结、智能问答（流式输出）
- **配置**: 同时只使用一个API

### 2.3 音频捕获
| 来源 | 实现方式 |
|------|----------|
| 文件上传 | FastAPI文件接收 |
| 麦克风 | sounddevice + WebSocket |
| 系统声音 | CABLE虚拟设备 + sounddevice |

### 2.4 模型配置
- **敏感信息**: 环境变量 (API Key)
- **模型路径/参数**: YAML配置文件
- **运行时**: 支持动态切换模型

## 3. 数据模型 (v2 - 取消会话层级)

### 3.1 项目层级
```
Project (项目)
  ├── 创建时间、描述、热词列表
  └── AudioFile (音频文件)
        ├── 名称、类型、创建时间、状态
        └── TranscriptSegment (转写段落)
              ├── 时间戳
              ├── 发言人ID
              ├── 文本内容(可编辑)
              └── 原始文本(用于对比)
```

### 3.2 核心表结构

```sql
-- 项目表
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    hotwords TEXT DEFAULT '',  -- 逗号分隔的热词
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 音频文件表 (直接关联项目，取消session层级)
CREATE TABLE audio_files (
    id INTEGER PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    audio_name TEXT NOT NULL,  -- 用户定义的音频名称
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    source_type TEXT NOT NULL,  -- file/microphone/system
    duration REAL,
    file_size INTEGER,
    status TEXT DEFAULT 'pending',  -- pending/processing/completed/failed/stopped
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 转写段落表
CREATE TABLE transcript_segments (
    id INTEGER PRIMARY KEY,
    audio_file_id INTEGER REFERENCES audio_files(id) ON DELETE CASCADE,
    speaker_id TEXT DEFAULT '0',
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    text TEXT NOT NULL,
    original_text TEXT,
    edited_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audio_project ON audio_files(project_id);
CREATE INDEX idx_segments_audio ON transcript_segments(audio_file_id);
```

## 4. API设计 (v2)

### 4.1 项目管理
```
GET    /api/projects              # 项目列表
POST   /api/projects              # 创建项目
GET    /api/projects/{id}         # 项目详情
PUT    /api/projects/{id}         # 更新项目
DELETE /api/projects/{id}         # 删除项目
PUT    /api/projects/{id}/hotwords # 更新热词
```

### 4.2 音频文件管理
```
GET    /api/projects/{id}/audio-files        # 项目音频列表
POST   /api/projects/{id}/upload             # 上传音频文件
POST   /api/projects/{id}/start-recording    # 开始实时录音
POST   /api/audio-files/{id}/stop            # 停止录音/转写
GET    /api/audio-files/{id}                 # 音频文件详情
GET    /api/audio-files/{id}/transcript      # 获取转写结果
PUT    /api/transcript-segments/{id}         # 编辑段落
DELETE /api/audio-files/{id}                 # 删除音频
```

### 4.3 实时音频流
```
WS     /ws/realtime/{project_id}             # 实时音频流
```

### 4.4 LLM调用 (流式输出)
```
POST   /api/llm/summarize                    # 总结转写内容
POST   /api/llm/chat                         # 智能问答 (SSE流式)
```

### 4.5 配置
```
GET    /api/config                           # 获取系统配置
GET    /api/audio/devices                    # 获取音频设备
```

## 5. 目录结构 (v2)

```
S2T/
├── backend/
│   ├── main.py
│   ├── config/
│   │   ├── settings.py
│   │   └── config.yaml
│   ├── core/
│   │   ├── asr/
│   │   │   └── engine.py
│   │   ├── llm/
│   │   │   ├── base.py
│   │   │   ├── ollama.py
│   │   │   ├── aliyun.py
│   │   │   └── deepseek.py
│   │   ├── audio/
│   │   │   └── capture.py
│   │   └── realtime.py
│   ├── api/
│   │   ├── projects.py
│   │   ├── audio_files.py
│   │   ├── llm.py
│   │   ├── realtime_routes.py
│   │   └── config_routes.py
│   ├── models/
│   │   ├── database.py
│   │   ├── project.py
│   │   ├── audio_file.py
│   │   └── transcript.py
│   └── utils/
│       └── audio_utils.py
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── Projects.vue
│   │   │   └── ProjectDetail.vue
│   │   ├── components/
│   │   │   ├── ProjectInfo.vue
│   │   │   ├── AudioList.vue
│   │   │   ├── MultiPanel.vue
│   │   │   ├── TranscriptCards.vue
│   │   │   ├── PlaybackReview.vue
│   │   │   └── AIChat.vue
│   │   ├── api/
│   │   ├── stores/
│   │   └── styles/
│   └── package.json
├── models/
├── data/
├── docs/
└── tests/
```

## 6. UI设计规范 (v2 - 苹果现代风格)

### 6.1 设计原则
- 极简主义，大量留白
- 毛玻璃效果 (backdrop-filter: blur)
- 细腻的阴影层次
- 流畅的动画过渡 (150-300ms)
- SF Pro字体风格

### 6.2 颜色系统
```scss
// 主色调
$primary: #007AFF;  // iOS蓝
$primary-hover: #0056CC;

// 背景色
$bg-primary: #F2F2F7;  // iOS浅灰
$bg-card: rgba(255, 255, 255, 0.8);  // 毛玻璃白
$bg-sidebar: rgba(255, 255, 255, 0.6);

// 文字色
$text-primary: #1C1C1E;
$text-secondary: #8E8E93;
$text-tertiary: #AEAEB2;

// 状态色
$success: #34C759;
$warning: #FF9500;
$danger: #FF3B30;
```

### 6.3 组件规范
- 圆角: 12px (卡片), 8px (按钮)
- 阴影: 0 2px 8px rgba(0, 0, 0, 0.04)
- 间距: 16px (组件间), 12px (元素间)
- 字体: -apple-system, BlinkMacSystemFont, 'SF Pro'

## 7. 并发控制

### 7.1 默认配置
- FunASR Paraformer: 默认2路并发
- 最大并发数: 4

### 7.2 实现方式
- 使用 `asyncio.Semaphore` 控制并发
- GPU显存监控，动态调整
- 用户可在设置页面配置

## 8. 配置文件示例

```yaml
# config.yaml
asr:
  engine: funasr
  model: iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch
  spk_model: iic/speech_campplus_sv_zh-cn_16k-common
  vad_model: iic/speech_fsmn_vad_zh-cn-16k-common-pytorch
  punc_model: iic/punc_ct-transformer_cn-en-common-vocab471067-large
  max_concurrent: 2

llm:
  provider: ollama  # ollama / aliyun / deepseek
  ollama:
    base_url: http://localhost:11434
    model: qwen3:8b
  aliyun:
    api_key: ${ALIYUN_API_KEY}
    model: qwen-plus
  deepseek:
    api_key: ${DEEPSEEK_API_KEY}
    model: deepseek-chat

audio:
  sample_rate: 16000
  chunk_duration: 0.5
  supported_formats:
    - wav
    - mp3
    - m4a
    - flac
    - ogg

database:
  path: ./data/s2t.db

storage:
  upload_dir: ./data/uploads
```

## 9. 开发阶段

### Phase 1: 核心链路
1. 后端框架搭建
2. 数据库模型
3. ASR引擎集成
4. 文件上传转写
5. 前端基础框架

### Phase 2: 功能完善
1. 项目管理界面
2. 转写结果编辑
3. LLM总结/问答
4. 热词配置

### Phase 3: 实时音频
1. WebSocket实时流
2. 麦克风捕获
3. 系统声音捕获

### Phase 4: UI重构 (v2)
1. 苹果现代风格设计
2. 项目详情页重构
3. 多功能详情页
4. 对照回顾功能
5. AI问答流式输出

## 10. 测试策略

### 10.1 单元测试
- ASR引擎封装测试
- LLM接口测试
- 数据库操作测试

### 10.2 集成测试
- 文件上传→转写→存储流程
- 实时音频→转写流程
- LLM调用流程

### 10.3 核心链路测试用例
1. 上传音频文件并成功转写
2. 实时麦克风录音并转写
3. 发言人分离正确性
4. 热词识别准确性
5. LLM总结生成
6. 转写结果编辑保存
7. AI问答流式输出
8. 对照回顾播放同步