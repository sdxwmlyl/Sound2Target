<template>
  <div class="settings-page">
    <header class="page-header">
      <h1>系统设置</h1>
      <p class="page-subtitle">所有配置修改后立即生效，无需重启服务</p>
    </header>

    <div class="settings-content">
      <!-- ───────── 文字模型配置 ───────── -->
      <div class="settings-card">
        <div class="card-header">
          <h3>🤖 文字模型</h3>
          <span class="card-desc">用于会议总结、问答对话、观点提取</span>
        </div>

        <div class="form-group">
          <label class="form-label">服务提供商</label>
          <div class="provider-tabs">
            <button v-for="p in textProviders" :key="p.key"
                    :class="['tab', { active: textForm.provider === p.key }]"
                    @click="textForm.provider = p.key">
              {{ p.icon }} {{ p.label }}
            </button>
          </div>
        </div>

        <!-- 动态表单 -->
        <div class="provider-fields" v-if="textForm.provider">
          <div class="form-group">
            <label class="form-label">Base URL</label>
            <input v-model="textForm.providers[textForm.provider].base_url"
                   class="form-input" placeholder="http://localhost:8081/v1" />
          </div>
          <div class="form-group">
            <label class="form-label">模型名称</label>
            <input v-model="textForm.providers[textForm.provider].model"
                   class="form-input" :placeholder="textModelPlaceholder" />
          </div>
          <div class="form-group" v-if="textForm.provider !== 'llamacpp'">
            <label class="form-label">API Key</label>
            <div class="input-with-icon">
              <input v-model="textForm.providers[textForm.provider].api_key"
                     :type="showKeys ? 'text' : 'password'"
                     class="form-input" placeholder="sk-..." />
              <button class="icon-btn" @click="showKeys = !showKeys"
                      :title="showKeys ? '隐藏' : '显示'">
                {{ showKeys ? '🙈' : '👁️' }}
              </button>
            </div>
          </div>
        </div>

        <div class="form-actions">
          <button class="btn btn-primary" @click="saveTextModel"
                  :disabled="saving">
            {{ saving ? '保存中...' : '保存文字模型配置' }}
          </button>
        </div>
      </div>

      <!-- ───────── 多模态模型配置 ───────── -->
      <div class="settings-card">
        <div class="card-header">
          <h3>👁️ 多模态模型</h3>
          <span class="card-desc">用于视频截图理解、图文混合内容分析</span>
        </div>

        <div class="form-group">
          <label class="form-label">服务提供商</label>
          <div class="provider-tabs">
            <button v-for="p in visionProviders" :key="p.key"
                    :class="['tab', { active: mmForm.provider === p.key }]"
                    @click="mmForm.provider = p.key">
              {{ p.icon }} {{ p.label }}
            </button>
          </div>
        </div>

        <div class="provider-fields">
          <div class="form-group">
            <label class="form-label">Base URL</label>
            <input v-model="mmForm.base_url" class="form-input"
                   placeholder="https://dashscope.aliyuncs.com/compatible-mode/v1" />
          </div>
          <div class="form-group">
            <label class="form-label">模型名称</label>
            <input v-model="mmForm.model" class="form-input"
                   :placeholder="visionModelPlaceholder" />
          </div>
          <div class="form-group">
            <label class="form-label">API Key</label>
            <div class="input-with-icon">
              <input v-model="mmForm.api_key"
                     :type="showKeys ? 'text' : 'password'"
                     class="form-input" placeholder="sk-..." />
              <button class="icon-btn" @click="showKeys = !showKeys">
                {{ showKeys ? '🙈' : '👁️' }}
              </button>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">最大输出 Token 数</label>
            <input v-model.number="mmForm.max_tokens" type="number"
                   class="form-input" min="256" max="16384" />
          </div>
        </div>

        <div class="form-actions">
          <button class="btn btn-primary" @click="saveMultimodal"
                  :disabled="saving">
            {{ saving ? '保存中...' : '保存多模态配置' }}
          </button>
        </div>
      </div>

      <!-- ───────── ASR 语音识别 ───────── -->
      <div class="settings-card">
        <div class="card-header">
          <h3>🎤 语音识别 (ASR)</h3>
          <span class="card-desc">FunASR Paraformer — 纯 CPU 推理，无需 GPU</span>
        </div>

        <div class="asr-grid">
          <div class="form-group">
            <label class="form-label">识别引擎</label>
            <select v-model="asrForm.engine" class="form-input">
              <option value="funasr">FunASR (推荐)</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">推理设备</label>
            <select v-model="asrForm.device" class="form-input">
              <option value="cpu">CPU (推荐，无需 GPU)</option>
              <option value="cuda">CUDA (需 NVIDIA GPU)</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">最大并发数</label>
            <select v-model.number="asrForm.max_concurrent" class="form-input">
              <option v-for="n in [1,2,3,4,5,6,7,8]" :key="n" :value="n">
                {{ n }} 路并发
              </option>
            </select>
          </div>
        </div>

        <!-- 硬件需求表 -->
        <div class="hw-requirements">
          <h4>📊 并发数 vs 硬件需求（CPU 模式）</h4>
          <table class="hw-table">
            <thead>
              <tr>
                <th>并发数</th>
                <th>内存 (RAM)</th>
                <th>CPU 核心</th>
                <th>推荐场景</th>
              </tr>
            </thead>
            <tbody>
              <tr :class="{ active: asrForm.max_concurrent === 1 }">
                <td><strong>1</strong></td>
                <td>≥ 4 GB</td>
                <td>2 核</td>
                <td>个人使用，单文件转写</td>
              </tr>
              <tr :class="{ active: asrForm.max_concurrent === 2 }">
                <td><strong>2</strong></td>
                <td>≥ 8 GB</td>
                <td>4 核</td>
                <td>小型团队，可同时处理 2 个音频</td>
              </tr>
              <tr :class="{ active: asrForm.max_concurrent === 4 }">
                <td><strong>4</strong></td>
                <td>≥ 16 GB</td>
                <td>8 核</td>
                <td>多人并发场景</td>
              </tr>
              <tr :class="{ active: asrForm.max_concurrent >= 6 }">
                <td><strong>6-8</strong></td>
                <td>≥ 32 GB</td>
                <td>16 核</td>
                <td>企业级，高并发服务</td>
              </tr>
            </tbody>
          </table>
          <p class="hw-note">
            ⚠️ 每路并发额外占用约 2-3 GB 内存（FunASR 模型 + PyTorch CPU 推理）。
            模型文件首次运行时自动从 ModelScope 下载到 <code>~/.cache/modelscope/</code>，
            总计约 3.5 GB，之后无需重新下载。
          </p>
        </div>

        <!-- 模型状态 -->
        <div class="model-status">
          <h4>📦 模型状态</h4>
          <div class="status-grid">
            <div class="status-item" :class="modelStatus.main ? 'ok' : 'missing'">
              <span class="status-icon">{{ modelStatus.main ? '✅' : '⏳' }}</span>
              <span>主模型 (Paraformer-large)</span>
              <span class="status-hint">{{ modelStatus.main ? '已下载' : '首次运行自动下载' }}</span>
            </div>
            <div class="status-item" :class="modelStatus.spk ? 'ok' : 'missing'">
              <span class="status-icon">{{ modelStatus.spk ? '✅' : '⏳' }}</span>
              <span>说话人分离 (CAM++)</span>
              <span class="status-hint">{{ modelStatus.spk ? '已下载' : '首次运行自动下载' }}</span>
            </div>
            <div class="status-item" :class="modelStatus.vad ? 'ok' : 'missing'">
              <span class="status-icon">{{ modelStatus.vad ? '✅' : '⏳' }}</span>
              <span>语音活动检测 (FSMN-VAD)</span>
              <span class="status-hint">{{ modelStatus.vad ? '已下载' : '首次运行自动下载' }}</span>
            </div>
            <div class="status-item" :class="modelStatus.punc ? 'ok' : 'missing'">
              <span class="status-icon">{{ modelStatus.punc ? '✅' : '⏳' }}</span>
              <span>标点恢复 (CT-Transformer)</span>
              <span class="status-hint">{{ modelStatus.punc ? '已下载' : '首次运行自动下载' }}</span>
            </div>
          </div>
        </div>

        <div class="form-actions">
          <button class="btn btn-primary" @click="saveASR" :disabled="saving">
            {{ saving ? '保存中...' : '保存 ASR 配置' }}
          </button>
        </div>
      </div>

      <!-- ───────── 音频设备 ───────── -->
      <div class="settings-card">
        <div class="card-header">
          <h3>🔊 音频设备</h3>
          <span class="card-desc">系统检测到的可用录音设备</span>
        </div>

        <div v-if="devicesLoading" class="loading">加载中...</div>
        <div v-else-if="audioDevices.length === 0" class="empty">未检测到音频设备</div>
        <div v-else class="device-list">
          <div v-for="device in audioDevices" :key="device.id" class="device-item">
            <div class="device-icon" :class="{ cable: device.is_cable }">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
              </svg>
            </div>
            <div class="device-info">
              <span class="device-name">{{ device.name }}</span>
              <span class="device-meta">
                {{ device.is_cable ? '虚拟音频线 (VB-CABLE)' : '物理麦克风' }}
                · {{ device.channels }} 声道
                · {{ device.sample_rate }} Hz
              </span>
            </div>
            <span class="device-badge" v-if="device.is_cable">推荐用于系统录音</span>
          </div>
        </div>
      </div>

      <!-- ───────── 保存提示 ───────── -->
      <transition name="toast">
        <div v-if="toastMessage" class="toast" :class="toastType">
          {{ toastMessage }}
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { configApi, audioDeviceApi } from '@/api'

const saving = ref(false)
const showKeys = ref(false)
const toastMessage = ref('')
const toastType = ref('success')

// ── Text LLM form ──
const textProviders = [
  { key: 'llamacpp', label: 'llama.cpp', icon: '🏠' },
  { key: 'aliyun',   label: '阿里百炼',  icon: '☁️' },
  { key: 'deepseek', label: 'DeepSeek',  icon: '🔮' },
]

const textForm = reactive({
  provider: 'llamacpp',
  providers: {
    llamacpp: { base_url: '', model: '', api_key: '' },
    aliyun:   { base_url: '', model: '', api_key: '' },
    deepseek: { base_url: '', model: '', api_key: '' },
  }
})

const textModelPlaceholder = computed(() => {
  const map = {
    llamacpp: 'Qwen3.6-35B-A3B-UD-Q4_K_M.gguf',
    aliyun:   'qwen-plus',
    deepseek: 'deepseek-chat',
  }
  return map[textForm.provider] || ''
})

// ── Multimodal form ──
const visionProviders = [
  { key: 'dashscope',  label: '阿里百炼',  icon: '☁️' },
  { key: 'deepseek',   label: 'DeepSeek',  icon: '🔮' },
  { key: 'openrouter', label: 'OpenRouter', icon: '🌐' },
  { key: 'custom',     label: '自定义',     icon: '⚙️' },
]

const mmForm = reactive({
  provider: 'dashscope',
  base_url: '',
  model: '',
  api_key: '',
  max_tokens: 2048,
})

const visionModelPlaceholder = computed(() => {
  const map = {
    dashscope:  'qwen-vl-max',
    deepseek:   'deepseek-chat',
    openrouter: 'anthropic/claude-sonnet-4',
    custom:     'your-vision-model',
  }
  return map[mmForm.provider] || ''
})

// ── ASR form ──
const asrForm = reactive({
  engine: 'funasr',
  device: 'cpu',
  max_concurrent: 2,
})

const modelStatus = reactive({
  main: false,
  spk: false,
  vad: false,
  punc: false,
})

// ── Audio devices ──
const audioDevices = ref([])
const devicesLoading = ref(false)

// ── Toast helper ──
function showToast(message, type = 'success') {
  toastMessage.value = message
  toastType.value = type
  setTimeout(() => { toastMessage.value = '' }, 3000)
}

// ── Load settings ──
async function loadSettings() {
  try {
    const res = await configApi.getSettings()
    const d = res.data

    // Text LLM
    if (d.llm) {
      textForm.provider = d.llm.provider || 'llamacpp'
      for (const pk of ['llamacpp', 'aliyun', 'deepseek']) {
        if (d.llm[pk]) {
          textForm.providers[pk].base_url = d.llm[pk].base_url || ''
          textForm.providers[pk].model = d.llm[pk].model || ''
          textForm.providers[pk].api_key = d.llm[pk].api_key || ''
        }
      }
    }

    // Multimodal
    if (d.multimodal) {
      mmForm.provider = d.multimodal.provider || 'dashscope'
      mmForm.base_url = d.multimodal.base_url || ''
      mmForm.model = d.multimodal.model || ''
      mmForm.api_key = d.multimodal.api_key || ''
      mmForm.max_tokens = d.multimodal.max_tokens || 2048
    }

    // ASR
    if (d.asr) {
      asrForm.engine = d.asr.engine || 'funasr'
      asrForm.device = d.asr.device || 'cpu'
      asrForm.max_concurrent = d.asr.max_concurrent || 2
      if (d.asr.model_status) {
        modelStatus.main = d.asr.model_status.main
        modelStatus.spk = d.asr.model_status.spk
        modelStatus.vad = d.asr.model_status.vad
        modelStatus.punc = d.asr.model_status.punc
      } else {
        modelStatus.main = d.asr.has_model
      }
    }
  } catch (e) {
    console.error('Failed to load settings:', e)
  }
}

// ── Save handlers ──
async function saveTextModel() {
  saving.value = true
  try {
    const payload = { llm: { provider: textForm.provider } }
    const prov = textForm.provider
    payload.llm[prov] = { ...textForm.providers[prov] }
    await configApi.updateSettings(payload)
    showToast('✅ 文字模型配置已保存')
  } catch (e) {
    showToast('❌ 保存失败: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    saving.value = false
  }
}

async function saveMultimodal() {
  saving.value = true
  try {
    await configApi.updateSettings({
      multimodal: { ...mmForm }
    })
    showToast('✅ 多模态模型配置已保存')
  } catch (e) {
    showToast('❌ 保存失败: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    saving.value = false
  }
}

async function saveASR() {
  saving.value = true
  try {
    await configApi.updateSettings({
      asr: { ...asrForm }
    })
    showToast('✅ ASR 配置已保存')
  } catch (e) {
    showToast('❌ 保存失败: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    saving.value = false
  }
}

// ── Load devices ──
async function loadDevices() {
  devicesLoading.value = true
  try {
    const res = await audioDeviceApi.getDevices()
    audioDevices.value = res.data.devices || []
  } catch (e) {
    console.error('Failed to load devices:', e)
  } finally {
    devicesLoading.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadSettings(), loadDevices()])
})
</script>

<style scoped>
/* ── Element Plus 兼容变量 ── */
:root {
  --s-bg:       #ffffff;
  --s-bg-alt:   #f5f7fa;
  --s-bg-hover: #ecf5ff;
  --s-border:   #e4e7ed;
  --s-border-h: #dcdfe6;
  --s-text-1:   #303133;
  --s-text-2:   #606266;
  --s-text-3:   #909399;
  --s-accent:   #409eff;
  --s-accent-h: #337ecc;
  --s-green:    #22c55e;
  --s-yellow:   #eab308;
  --s-red:      #ef4444;
}

.settings-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px 20px 60px;
}

.page-header {
  margin-bottom: 28px;
}
.page-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--s-text-1);
  margin: 0 0 6px;
}
.page-subtitle {
  font-size: 14px;
  color: var(--s-text-3);
  margin: 0;
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 24px;
  background: #f0f2f5;
  border-radius: 20px;
}

/* ── Card ── */
.settings-card {
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  transition: border-color 0.2s, box-shadow 0.2s;
}
.settings-card:hover {
  border-color: #dcdfe6;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.card-header {
  margin-bottom: 20px;
}
.card-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 4px;
}
.card-desc {
  font-size: 13px;
  color: #909399;
}

/* ── Form ── */
.form-group {
  margin-bottom: 16px;
}
.form-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #606266;
  margin-bottom: 6px;
}
.form-input {
  width: 100%;
  padding: 10px 14px;
  background: #ffffff;
  border: 1px solid #dcdfe6;
  border-radius: 10px;
  color: #303133;
  font-size: 14px;
  font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  box-sizing: border-box;
}
.form-input:focus {
  border-color: #409eff;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.15);
}
.form-input::placeholder {
  color: #c0c4cc;
}
select.form-input {
  cursor: pointer;
  appearance: none;
  background-color: #ffffff;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%23999' fill='none' stroke-width='1.5'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 32px;
}

.input-with-icon {
  display: flex;
  gap: 8px;
  align-items: center;
}
.input-with-icon .form-input {
  flex: 1;
}
.icon-btn {
  width: 38px;
  height: 38px;
  border: 1px solid #dcdfe6;
  border-radius: 10px;
  background: #f5f7fa;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border-color 0.2s;
}
.icon-btn:hover {
  border-color: #409eff;
}

/* ── Provider tabs ── */
.provider-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.provider-fields {
  margin-top: 16px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid #e8eff7;
}
.tab {
  padding: 8px 16px;
  border-radius: 10px;
  border: 1px solid #dcdfe6;
  background: #f5f7fa;
  color: #606266;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.tab:hover {
  border-color: #409eff;
  color: #303133;
  background: #ecf5ff;
}
.tab.active {
  background: #409eff;
  border-color: #409eff;
  color: #fff;
}

/* ── ASR grid ── */
.asr-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

/* ── Hardware table ── */
.hw-requirements {
  margin-top: 20px;
  padding: 20px;
  background: #f0f5ff;
  border-radius: 12px;
  border: 1px solid #d4e4ff;
}
.hw-requirements h4 {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 12px;
}
.hw-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 13px;
  border: 1px solid #d4e4ff;
  border-radius: 8px;
  overflow: hidden;
}
.hw-table th {
  text-align: left;
  padding: 10px 12px;
  border-bottom: 2px solid #b8d4ff;
  color: #303133;
  font-weight: 600;
  background: #e6f0ff;
}
.hw-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #e8eff7;
  color: #303133;
  background: #ffffff;
}
.hw-table tr:last-child td {
  border-bottom: none;
}
.hw-table tr.active td {
  background: #dbeafe;
  color: #1d4ed8;
  font-weight: 600;
}
.hw-note {
  font-size: 12px;
  color: #606266;
  margin: 12px 0 0;
  line-height: 1.6;
}
.hw-note code {
  background: #ffffff;
  border: 1px solid #d4e4ff;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 12px;
  color: #303133;
}

/* ── Model status ── */
.model-status {
  margin-top: 20px;
  padding: 20px;
  background: #f0f9eb;
  border-radius: 12px;
  border: 1px solid #c2e7b0;
}
.model-status h4 {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 12px;
}
.status-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}
.status-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 10px;
  background: #ffffff;
  border: 1px solid #c2e7b0;
  font-size: 13px;
  color: #303133;
}
.status-item.ok {
  border-left: 3px solid #22c55e;
}
.status-item.missing {
  border-left: 3px solid #eab308;
}
.status-icon {
  font-size: 16px;
  flex-shrink: 0;
}
.status-hint {
  margin-left: auto;
  font-size: 11px;
  color: #909399;
}

/* ── Device list ── */
.device-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.device-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e0e6ed;
}
.device-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #ecf5ff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
}
.device-icon svg {
  width: 20px;
  height: 20px;
}
.device-icon.cable {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}
.device-info {
  flex: 1;
}
.device-name {
  display: block;
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}
.device-meta {
  font-size: 12px;
  color: #909399;
}
.device-badge {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 20px;
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
  font-weight: 500;
  white-space: nowrap;
}

/* ── Buttons ── */
.form-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid #e4e7ed;
  margin-top: 4px;
}
.btn {
  padding: 10px 24px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-primary {
  background: #409eff;
  color: #fff;
}
.btn-primary:hover:not(:disabled) {
  background: #337ecc;
}
.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ── Toast ── */
.toast {
  position: fixed;
  bottom: 32px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  z-index: 9999;
  box-shadow: 0 8px 32px rgba(0,0,0,0.2);
}
.toast.success {
  background: #22c55e;
  color: #fff;
}
.toast.error {
  background: #ef4444;
  color: #fff;
}
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}

/* ── Misc ── */
.loading, .empty {
  text-align: center;
  padding: 32px 16px;
  color: #909399;
  font-size: 14px;
}

/* ── Responsive ── */
@media (max-width: 640px) {
  .asr-grid {
    grid-template-columns: 1fr;
  }
  .status-grid {
    grid-template-columns: 1fr;
  }
  .provider-tabs {
    gap: 6px;
  }
  .tab {
    padding: 6px 12px;
    font-size: 12px;
  }
}
</style>
