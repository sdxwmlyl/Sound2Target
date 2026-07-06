# S2T 依赖清单

## 后端依赖 (已安装)

| 包名 | 版本 | 用途 |
|-----|------|------|
| fastapi | 0.104.1 | Web框架 |
| funasr | 1.3.1 | ASR引擎 |
| torch | 2.5.1 | 深度学习 |
| pydub | 0.25.1 | 音频处理 |
| sounddevice | 0.5.5 | 音频捕获 |
| aiofiles | 24.1.0 | 异步文件 |
| pyyaml | (系统自带) | 配置解析 |
| uvicorn | 0.24.0 | ASGI服务器 |

## 前端依赖 (已安装)

| 包名 | 版本 | 用途 |
|-----|------|------|
| vue | 3.5.34 | 前端框架 |
| element-plus | 2.14.0 | UI组件 |
| axios | 1.16.1 | HTTP请求 |
| pinia | 2.3.1 | 状态管理 |
| vue-router | 4.6.4 | 路由 |
| vite | 5.x | 构建工具 |

## 安装命令

### 后端
```bash
cd S2T/backend
pip install -r requirements.txt
```

### 前端
```bash
cd S2T/frontend
npm install
```

## 注意事项

1. **FunASR模型下载**: 首次运行会自动下载模型 (~1GB)
2. **Ollama**: 需单独安装并启动 (`ollama serve`)
3. **CABLE驱动**: 系统声音捕获需安装 VB-Audio Virtual Cable