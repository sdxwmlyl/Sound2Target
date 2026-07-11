# video_analysis Skill

视频内容分析 Skill：输入视频 URL，自动完成全链路内容提取和分析。

## 触发条件

当用户提到以下内容时使用本 Skill：
- "分析这个视频" / "看看这个视频讲了什么"
- "提取视频中的XX" / "从视频里找XX"
- 提供了 Bilibili / YouTube / 其他视频平台的 URL
- "视频总结" / "视频内容提取"
- "帮我看看这个评测/发布会/讲座"

## 核心能力

| 能力 | 说明 |
|------|------|
| 音频转写 | yt-dlp 下载音频 → S2T ASR 转写（带时间戳） |
| 视觉帧捕获 | 浏览器截图 + 文案驱动关键帧定位 |
| 多模态识别 | 调用多模态大模型识别图表/表格/画面文字 |
| 双轨融合 | 音频文案 + 视觉帧描述 → 去重合并 |
| 自定义总结 | 按用户要求生成结构化分析报告 |

## 使用方式

### 方式 1：直接调用 MCP 工具（推荐）

```
s2t_mcp.analyze_video(
    url="https://www.bilibili.com/video/BV13sMi63EAQ/",
    summary_prompt="提取评测维度、指标和对比思路",
    sample_interval=30
)
```

### 方式 2：分步调用（更灵活）

```
# Step 1: 启动分析
s2t_mcp.analyze_video(url=..., summary_prompt=..., enable_frame_capture=false)

# Step 2: 如果需要帧捕获，手动用浏览器截图
# （当多模态API不可用时，用这种方式）

# Step 3: 查询结果
s2t_mcp.check_video_analysis(task_id=...)
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| url | string | 必填 | 视频 URL |
| summary_prompt | string | "请提取核心内容" | 自定义总结要求 |
| project_name | string | 自动生成 | 项目名称 |
| sample_interval | int | 30 | 视觉帧采样间隔（秒） |
| enable_frame_capture | bool | true | 是否启用视觉帧捕获 |
| timeout | int | 600 | 超时时间（秒） |

## 系统配置要求

### config.yaml 新增配置

```yaml
# 视频分析
video:
  yt_dlp_path: "yt-dlp"  # 需要 pip install yt-dlp
  sample_interval: 30
  max_duration: 3600

# 多模态大模型（用于图表识别）
multimodal:
  provider: "dashscope"
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  model: "qwen-vl-max"
  api_key: "YOUR_API_KEY"  # 或设置环境变量 MULTIMODAL_API_KEY
```

### 依赖检查

```bash
# yt-dlp（必须）
pip install yt-dlp

# 多模态API（可选，不配置则跳过图表识别）
# 支持：DashScope / OpenAI / 任何 OpenAI 兼容 API
```

## 输出格式

```json
{
  "task_id": 1,
  "video_title": "视频标题",
  "video_duration": 1007.2,
  "transcript_segments": 419,
  "frames_captured": 34,
  "frames_analyzed": 34,
  "content_items": 56,
  "summary": "# 结构化总结\n\n## 维度1\n...",
  "project_id": 39
}
```

## 工作流程

```
用户输入 URL + 总结要求
    │
    ├── Step 1: yt-dlp 下载音频（~10s）
    ├── Step 2: S2T 转写（~30s）
    ├── Step 3: 文案关键词筛选（~1s）
    ├── Step 4: 视觉帧捕获（~3min，可选）
    ├── Step 5: 多模态图表识别（~2min，可选）
    ├── Step 6: 双轨融合（~1s）
    └── Step 7: 自定义总结（~30s）
    
    总耗时：~6-10 分钟（取决于视频长度和配置）
```

## 降级策略

| 场景 | 降级行为 |
|------|---------|
| 多模态 API 未配置 | 跳过图表识别，仅用文案生成总结 |
| yt-dlp 不可用 | 提示用户安装，或手动上传音频 |
| 浏览器不可用 | 跳过帧捕获，仅用文案分析 |
| 视频过长（>1h） | 提示用户，可选择分段处理 |

## 注意事项

1. **Bilibili 登录态**：部分视频需要登录才能访问，确保浏览器有登录 Cookie
2. **多模态 API 费用**：每次分析约消耗 30-50 次多模态 API 调用
3. **超时设置**：长视频（>30分钟）建议设置 timeout=1200
4. **存储空间**：临时文件在 `data/video_temp/` 目录，分析完成后可清理
