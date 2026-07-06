<template>
  <div class="settings-page">
    <header class="page-header">
      <h1>系统设置</h1>
    </header>
    
    <div class="settings-content">
      <!-- 系统配置 -->
      <div class="settings-card">
        <h3>系统配置</h3>
        <div class="config-list">
          <div class="config-item">
            <span class="config-label">LLM提供商</span>
            <span class="config-value">{{ config?.llm_provider || '-' }}</span>
          </div>
          <div class="config-item">
            <span class="config-label">ASR引擎</span>
            <span class="config-value">{{ config?.asr_engine || '-' }}</span>
          </div>
          <div class="config-item">
            <span class="config-label">最大并发数</span>
            <span class="config-value">{{ config?.max_concurrent || 2 }}</span>
          </div>
          <div class="config-item">
            <span class="config-label">支持格式</span>
            <span class="config-value">{{ config?.supported_formats?.join(', ') || '-' }}</span>
          </div>
        </div>
      </div>
      
      <!-- API配置说明 -->
      <div class="settings-card">
        <h3>API配置</h3>
        <div class="info-box">
          <p>配置文件位于：<code>backend/config/config.yaml</code></p>
          <p>API密钥通过环境变量设置：</p>
          <ul>
            <li><code>ALIYUN_API_KEY</code> - 阿里百炼API密钥</li>
            <li><code>DEEPSEEK_API_KEY</code> - Deepseek API密钥</li>
          </ul>
        </div>
      </div>
      
      <!-- 音频设备 -->
      <div class="settings-card">
        <h3>音频设备</h3>
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
              <span class="device-meta">{{ device.is_cable ? 'CABLE虚拟设备' : '麦克风' }} · {{ device.channels }}声道</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { configApi, audioDeviceApi } from '@/api'

const config = ref(null)
const audioDevices = ref([])
const devicesLoading = ref(false)

onMounted(async () => {
  await loadConfig()
  await loadDevices()
})

async function loadConfig() {
  try {
    const res = await configApi.get()
    config.value = res.data
  } catch (e) {
    console.error('Load config error:', e)
  }
}

async function loadDevices() {
  devicesLoading.value = true
  try {
    const res = await audioDeviceApi.getDevices()
    audioDevices.value = res.data.devices || []
  } catch (e) {
    console.error('Load devices error:', e)
  } finally {
    devicesLoading.value = false
  }
}
</script>

<style scoped>
.settings-page {
  min-height: 100vh;
  background: #F2F2F7;
}

.page-header {
  padding: 20px 24px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 0.5px solid rgba(0, 0, 0, 0.1);
}

.page-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: #1C1C1E;
}

.settings-content {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px 24px;
}

.settings-card {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 16px;
  border: 0.5px solid rgba(0, 0, 0, 0.1);
  padding: 20px;
  margin-bottom: 16px;
}

.settings-card h3 {
  font-size: 17px;
  font-weight: 600;
  color: #1C1C1E;
  margin: 0 0 16px 0;
}

.config-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.config-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #F2F2F7;
  border-radius: 10px;
}

.config-label {
  font-size: 14px;
  color: #8E8E93;
}

.config-value {
  font-size: 14px;
  font-weight: 500;
  color: #1C1C1E;
}

.info-box {
  padding: 16px;
  background: #F2F2F7;
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.6;
  color: #3C3C43;
}

.info-box p {
  margin: 0 0 8px 0;
}

.info-box ul {
  margin: 8px 0 0 0;
  padding-left: 20px;
}

.info-box li {
  margin-bottom: 4px;
}

.info-box code {
  background: rgba(0, 122, 255, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  color: #007AFF;
}

.loading,
.empty {
  padding: 20px;
  text-align: center;
  color: #8E8E93;
  font-size: 14px;
}

.device-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.device-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #F2F2F7;
  border-radius: 10px;
}

.device-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 122, 255, 0.1);
  color: #007AFF;
}

.device-icon.cable {
  background: rgba(52, 199, 89, 0.1);
  color: #34C759;
}

.device-icon svg {
  width: 20px;
  height: 20px;
}

.device-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.device-name {
  font-size: 14px;
  font-weight: 500;
  color: #1C1C1E;
}

.device-meta {
  font-size: 12px;
  color: #8E8E93;
}
</style>