<template>
  <div class="audio-list">
    <div class="list-header">
      <h3>音频列表</h3>
      <div class="header-actions">
        <button class="action-btn primary" @click="toggleAddPanel">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          <span>添加</span>
        </button>
        <button class="action-btn" @click="$emit('show-ai-chat')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          <span>AI问答</span>
        </button>
      </div>
    </div>
    
    <!-- 添加音频面板（内嵌） -->
    <div v-if="showAddPanel" class="add-panel">
      <div class="add-form">
        <div class="form-row">
          <label>名称</label>
          <input v-model="newAudio.name" placeholder="输入音频名称" class="form-input" />
        </div>
        
        <div class="form-row">
          <label>来源</label>
          <div class="source-btns">
            <button 
              class="source-btn" 
              :class="{ active: newAudio.sourceType === 'file' }"
              @click="newAudio.sourceType = 'file'"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              上传文件
            </button>
            <button 
              class="source-btn" 
              :class="{ active: newAudio.sourceType === 'microphone' }"
              :disabled="hasActiveRecording"
              @click="newAudio.sourceType = 'microphone'"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
              </svg>
              麦克风
            </button>
            <button 
              class="source-btn" 
              :class="{ active: newAudio.sourceType === 'system' }"
              :disabled="hasActiveRecording"
              @click="newAudio.sourceType = 'system'"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
                <line x1="8" y1="21" x2="16" y2="21"/>
                <line x1="12" y1="17" x2="12" y2="21"/>
              </svg>
              系统
            </button>
            <button 
              class="source-btn" 
              :class="{ active: newAudio.sourceType === 'url' }"
              @click="newAudio.sourceType = 'url'"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
              </svg>
              URL
            </button>
          </div>
          <div v-if="newAudio.sourceType === 'system'" class="system-tip">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="16" x2="12" y2="12"/>
              <line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
            <span>请先在 Windows 声音设置中将输出设备改为 "CABLE Input (VB-Audio Virtual Cable)"</span>
          </div>
        </div>
        
        <!-- 文件选择 -->
        <div v-if="newAudio.sourceType === 'file'" class="form-row">
          <div class="file-select" @click="triggerFileInput" @drop.prevent="handleDrop" @dragover.prevent>
            <input 
              ref="fileInput" 
              type="file" 
              accept=".wav,.mp3,.m4a,.flac,.ogg" 
              multiple 
              @change="handleFileSelect" 
              style="display: none"
            />
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            <span v-if="selectedFiles.length === 0">点击选择文件</span>
            <span v-else>已选 {{ selectedFiles.length }} 个文件</span>
          </div>
        </div>
        
        <!-- 录音状态 -->
        <div v-if="newAudio.sourceType !== 'file' && newAudio.sourceType !== 'url' && isRecording" class="recording-status">
          <div class="recording-indicator">
            <span class="dot"></span>
            <span>录音中 {{ formatDuration(recordingDuration) }}</span>
          </div>
          <div class="realtime-text" v-if="realtimeSegments.length > 0">
            <div v-for="(seg, i) in realtimeSegments.slice(-5)" :key="i" class="text-item">
              <span class="text-speaker">{{ seg.speaker_id }}:</span>
              <span class="text-content">{{ seg.text }}</span>
            </div>
          </div>
        </div>

        <!-- URL输入 -->
        <div v-if="newAudio.sourceType === 'url'" class="url-input-section">
          <div class="form-row">
            <label>链接</label>
            <input
              v-model="newAudio.url"
              placeholder="输入视频/音频URL（支持YouTube、B站等）"
              class="form-input"
              @keyup.enter="handleDownloadUrl"
            />
          </div>
          <div v-if="urlDownloading" class="url-downloading">
            <div class="spinner"></div>
            <span>正在下载音频，请稍候...</span>
          </div>
        </div>
        
        <div class="form-actions">
          <button class="btn-cancel" @click="cancelAdd">取消</button>
          <button 
            v-if="newAudio.sourceType === 'file'"
            class="btn-submit" 
            :disabled="!canSubmitFile"
            @click="handleUpload"
          >
            上传并转写
          </button>
          <button
            v-else-if="newAudio.sourceType === 'url'"
            class="btn-submit"
            :disabled="!newAudio.url || urlDownloading"
            @click="handleDownloadUrl"
          >
            {{ urlDownloading ? '下载中...' : '下载并转写' }}
          </button>
          <button 
            v-else-if="!isRecording"
            class="btn-submit recording" 
            :disabled="!newAudio.name || hasActiveRecording"
            @click="startRecording"
          >
            开始录音
          </button>
          <button 
            v-else
            class="btn-stop" 
            @click="stopRecording"
          >
            停止录音
          </button>
        </div>
      </div>
    </div>
    
    <!-- 音频列表 -->
    <div class="list-content">
      <div 
        v-for="audio in audioFiles" 
        :key="audio.id" 
        class="audio-item"
      >
        <div class="item-icon" :class="audio.source_type">
          <svg v-if="audio.source_type === 'file'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
          <svg v-else-if="audio.source_type === 'microphone'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
          </svg>
          <svg v-else-if="audio.source_type === 'url'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
            <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
            <line x1="8" y1="21" x2="16" y2="21"/>
            <line x1="12" y1="17" x2="12" y2="21"/>
          </svg>
        </div>
        
        <div class="item-info">
          <div class="item-name">
            {{ audio.audio_name }}
            <span class="name-type">{{ getTypeLabel(audio.source_type) }}</span>
          </div>
          <div class="item-meta">
            <span v-if="audio.duration" class="meta-duration">时长 {{ formatDuration(audio.duration) }}</span>
            <span class="meta-time">创建 {{ formatDate(audio.created_at) }}</span>
          </div>
        </div>
        
        <span class="status-badge" :class="audio.status">
          {{ getStatusLabel(audio.status) }}
        </span>
        
        <div class="item-actions">
          <button 
            v-if="audio.status === 'processing'" 
            class="action-icon danger" 
            @click="handleStop(audio)"
            title="停止"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="6" y="6" width="12" height="12" rx="2"/>
            </svg>
          </button>
          <button 
            v-if="audio.status === 'completed'" 
            class="action-icon" 
            @click="$emit('play', audio)"
            title="播放"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="5 3 19 12 5 21 5 3"/>
            </svg>
          </button>
          <button 
            class="action-icon danger" 
            @click="$emit('delete', audio.id)"
            title="删除"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
            </svg>
          </button>
        </div>
      </div>
      
      <div v-if="audioFiles.length === 0 && !showAddPanel" class="empty-state">
        <p>暂无音频文件</p>
        <button class="action-btn primary" @click="toggleAddPanel">添加音频</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { projectApi, audioApi } from '@/api'
import { ElMessage } from 'element-plus'

const props = defineProps({
  audioFiles: Array,
  projectId: String,
  hasActiveRecording: Boolean
})

const emit = defineEmits(['refresh', 'play', 'delete', 'show-ai-chat'])

const showAddPanel = ref(false)
const fileInput = ref(null)
const selectedFiles = ref([])
const newAudio = ref({ name: '', sourceType: 'file', url: '' })
const urlDownloading = ref(false)

// 录音相关
const isRecording = ref(false)
const recordingDuration = ref(0)
const realtimeSegments = ref([])
let ws = null
let durationTimer = null
let sessionId = ''

const canSubmitFile = computed(() => {
  return newAudio.value.name && selectedFiles.value.length > 0
})

function toggleAddPanel() {
  showAddPanel.value = !showAddPanel.value
  if (showAddPanel.value) {
    newAudio.value = { name: '', sourceType: 'file', url: '' }
    selectedFiles.value = []
  }
}

function cancelAdd() {
  showAddPanel.value = false
  urlDownloading.value = false
  if (isRecording.value) {
    stopRecording()
  }
}

function triggerFileInput() {
  fileInput.value.click()
}

function handleFileSelect(e) {
  selectedFiles.value = Array.from(e.target.files)
}

function handleDrop(e) {
  selectedFiles.value = Array.from(e.dataTransfer.files)
}

async function handleUpload() {
  if (!canSubmitFile.value) return
  
  for (const file of selectedFiles.value) {
    try {
      await projectApi.upload(props.projectId, newAudio.value.name, file)
      ElMessage.success('上传成功')
    } catch (e) {
      ElMessage.error('上传失败')
    }
  }
  
  showAddPanel.value = false
  emit('refresh')
}

async function handleDownloadUrl() {
  if (!newAudio.value.url) return

  urlDownloading.value = true
  try {
    await projectApi.downloadUrl(
      props.projectId,
      newAudio.value.url,
      newAudio.value.name || ''
    )
    ElMessage.success('下载成功，正在转写...')
    showAddPanel.value = false
    emit('refresh')
  } catch (e) {
    const msg = e.response?.data?.detail || e.message || '下载失败'
    ElMessage.error(msg)
  } finally {
    urlDownloading.value = false
  }
}

function startRecording() {
  if (!newAudio.value.name) return
  
  sessionId = `session_${Date.now()}`
  console.log('Connecting to WebSocket...')
  ws = new WebSocket(`ws://localhost:8000/api/realtime/ws/${props.projectId}?session_id=${sessionId}`)
  
  // 心跳定时器
  let heartbeatTimer = null
  
  ws.onopen = () => {
    console.log('WebSocket connected, sending start_recording...')
    ws.send(JSON.stringify({
      type: 'start_recording',
      source_type: newAudio.value.sourceType,
      hotwords: '',
      audio_name: newAudio.value.name
    }))
    
    isRecording.value = true
    recordingDuration.value = 0
    realtimeSegments.value = []
    durationTimer = setInterval(() => {
      recordingDuration.value++
    }, 1000)
    
    // 每30秒发送心跳
    heartbeatTimer = setInterval(() => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000)
  }
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    console.log('WebSocket message:', data.type)
    if (data.type === 'recording_stopped') {
      ElMessage.success('录音已停止')
      cleanupRecording()
      emit('refresh')
    }
  }
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
    ElMessage.error('连接失败')
    if (heartbeatTimer) clearInterval(heartbeatTimer)
    cleanupRecording()
  }
  
  ws.onclose = () => {
    console.log('WebSocket closed')
    if (heartbeatTimer) clearInterval(heartbeatTimer)
    if (isRecording.value) {
      ElMessage.warning('连接已断开')
      cleanupRecording()
    }
  }
}

function stopRecording() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'stop_recording' }))
  }
  
  setTimeout(() => {
    cleanupRecording()
    showAddPanel.value = false
    emit('refresh')
    ElMessage.success('录音完成')
  }, 500)
}

function cleanupRecording() {
  isRecording.value = false
  if (durationTimer) {
    clearInterval(durationTimer)
    durationTimer = null
  }
  if (ws) {
    ws.close()
    ws = null
  }
}

async function handleStop(audio) {
  try {
    await audioApi.stop(audio.id)
    ElMessage.success('已停止')
    emit('refresh')
  } catch (e) {
    ElMessage.error('停止失败')
  }
}

function getTypeLabel(type) {
  const labels = { file: '文件', microphone: '麦克风', system: '系统', url: 'URL' }
  return labels[type] || type
}

function getStatusLabel(status) {
  const labels = { pending: '待转换', processing: '转写中', completed: '已完成', failed: '失败', stopped: '已停止' }
  return labels[status] || status
}

function formatTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function formatDuration(seconds) {
  if (!seconds || seconds <= 0) return ''
  const hours = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')
  const hours = date.getHours().toString().padStart(2, '0')
  const mins = date.getMinutes().toString().padStart(2, '0')
  return `${month}/${day} ${hours}:${mins}`
}
</script>

<style scoped>
.audio-list {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 16px;
  border: 0.5px solid rgba(0, 0, 0, 0.1);
  height: 100%;
  display: flex;
  flex-direction: column;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 0.5px solid rgba(0, 0, 0, 0.1);
}

.list-header h3 {
  font-size: 15px;
  font-weight: 600;
  color: #1C1C1E;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: rgba(142, 142, 147, 0.12);
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #1C1C1E;
  cursor: pointer;
}

.action-btn:hover {
  background: rgba(142, 142, 147, 0.2);
}

.action-btn.primary {
  background: #007AFF;
  color: white;
}

.action-btn.primary:hover {
  background: #0056CC;
}

/* 添加面板 */
.add-panel {
  padding: 16px;
  background: #F2F2F7;
  border-bottom: 0.5px solid rgba(0, 0, 0, 0.1);
}

.add-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.form-row label {
  font-size: 13px;
  font-weight: 500;
  color: #8E8E93;
  min-width: 40px;
}

.form-input {
  flex: 1;
  padding: 8px 12px;
  font-size: 14px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  background: white;
}

.form-input:focus {
  outline: none;
  border-color: #007AFF;
}

.source-btns {
  display: flex;
  gap: 8px;
}

.source-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background: white;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 6px;
  font-size: 12px;
  color: #1C1C1E;
  cursor: pointer;
}

.source-btn:hover:not(:disabled) {
  border-color: #007AFF;
  color: #007AFF;
}

.source-btn.active {
  background: rgba(0, 122, 255, 0.1);
  border-color: #007AFF;
  color: #007AFF;
}

.source-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.system-tip {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  background: rgba(255, 149, 0, 0.1);
  border-radius: 8px;
  font-size: 12px;
  color: #FF9500;
  line-height: 1.4;
}

.system-tip svg {
  flex-shrink: 0;
  margin-top: 1px;
}

.file-select {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: white;
  border: 1px dashed rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  cursor: pointer;
  color: #8E8E93;
  font-size: 13px;
}

.file-select:hover {
  border-color: #007AFF;
  color: #007AFF;
}

.recording-status {
  padding: 12px;
  background: white;
  border-radius: 8px;
}

.recording-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #FF3B30;
  margin-bottom: 8px;
}

.dot {
  width: 8px;
  height: 8px;
  background: #FF3B30;
  border-radius: 50%;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.realtime-text {
  max-height: 100px;
  overflow-y: auto;
}

.text-item {
  display: flex;
  gap: 4px;
  padding: 2px 0;
  font-size: 12px;
}

.text-speaker {
  color: #8E8E93;
}

.text-content {
  color: #1C1C1E;
}

.url-input-section {
  margin-top: 4px;
}

.url-downloading {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 0;
  color: #007AFF;
  font-size: 13px;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(0, 122, 255, 0.2);
  border-top-color: #007AFF;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.btn-cancel {
  padding: 8px 16px;
  background: rgba(142, 142, 147, 0.12);
  border: none;
  border-radius: 8px;
  font-size: 13px;
  color: #1C1C1E;
  cursor: pointer;
}

.btn-submit {
  padding: 8px 16px;
  background: #007AFF;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  color: white;
  cursor: pointer;
}

.btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-submit.recording {
  background: #34C759;
}

.btn-stop {
  padding: 8px 16px;
  background: #FF3B30;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  color: white;
  cursor: pointer;
}

/* 列表内容 */
.list-content {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.audio-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-bottom: 0.5px solid rgba(0, 0, 0, 0.06);
}

.item-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.item-icon.file {
  background: rgba(0, 122, 255, 0.1);
  color: #007AFF;
}

.item-icon.microphone {
  background: rgba(255, 149, 0, 0.1);
  color: #FF9500;
}

.item-icon.system {
  background: rgba(52, 199, 89, 0.1);
  color: #34C759;
}

.item-icon.url {
  background: rgba(88, 86, 214, 0.1);
  color: #5856D6;
}

.item-icon svg {
  width: 18px;
  height: 18px;
}

.item-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.item-name {
  font-size: 14px;
  font-weight: 500;
  color: #1C1C1E;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
  display: flex;
  align-items: center;
  gap: 8px;
}

.name-type {
  font-size: 11px;
  font-weight: 400;
  color: #8E8E93;
  background: rgba(142, 142, 147, 0.12);
  padding: 1px 6px;
  border-radius: 4px;
  flex-shrink: 0;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #8E8E93;
  line-height: 1.4;
}

.status-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  flex-shrink: 0;
}

.status-badge.pending {
  background: rgba(142, 142, 147, 0.12);
  color: #8E8E93;
}

.status-badge.processing {
  background: rgba(255, 149, 0, 0.12);
  color: #FF9500;
}

.status-badge.completed {
  background: rgba(52, 199, 89, 0.12);
  color: #34C759;
}

.status-badge.failed {
  background: rgba(255, 59, 48, 0.12);
  color: #FF3B30;
}

.status-badge.stopped {
  background: rgba(142, 142, 147, 0.12);
  color: #8E8E93;
}

.item-actions {
  display: flex;
  gap: 6px;
}

.action-icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 122, 255, 0.1);
  border: none;
  color: #007AFF;
  cursor: pointer;
}

.action-icon:hover {
  background: rgba(0, 122, 255, 0.2);
}

.action-icon.danger {
  background: rgba(255, 59, 48, 0.1);
  color: #FF3B30;
}

.action-icon svg {
  width: 14px;
  height: 14px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 30px 16px;
  color: #8E8E93;
}

.empty-state p {
  font-size: 14px;
  margin: 0 0 12px 0;
}
</style>