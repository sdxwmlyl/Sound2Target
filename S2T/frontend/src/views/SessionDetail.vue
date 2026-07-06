<template>
  <div class="session-detail">
    <el-page-header @back="$router.push(`/project/${projectId}`)" title="返回项目">
      <template #content>
        <span>{{ session?.name || '会话详情' }}</span>
      </template>
    </el-page-header>
    
    <el-row :gutter="20" class="main-content">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>音频文件</span>
              <el-upload
                ref="uploadRef"
                :action="`/api/sessions/${sessionId}/upload`"
                :on-success="handleUploadSuccess"
                :on-error="handleUploadError"
                :accept="supportedFormats"
                :show-file-list="false"
                multiple
              >
                <el-button type="primary">
                  <el-icon><Upload /></el-icon> 上传音频
                </el-button>
              </el-upload>
            </div>
          </template>
          
          <el-table :data="audioFiles" v-loading="loading" stripe>
            <el-table-column prop="filename" label="文件名" />
            <el-table-column label="时长" width="100">
              <template #default="{ row }">
                {{ formatDuration(row.duration) }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="statusType(row.status)">
                  {{ statusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="上传时间" width="180" />
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button 
                  size="small" 
                  type="primary" 
                  :disabled="row.status === 'processing'"
                  @click="startTranscribe(row.id)"
                >
                  转写
                </el-button>
                <el-button 
                  size="small" 
                  :disabled="row.status !== 'completed'"
                  @click="$router.push(`/transcript/${row.id}`)"
                >
                  查看
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
        
        <el-card v-if="session?.source_type !== 'file'" class="realtime-card">
          <template #header>
            <span>实时录音</span>
          </template>
          
          <div class="realtime-controls">
            <el-button type="success" @click="startRecording" :disabled="isRecording">
              <el-icon><Microphone /></el-icon> 开始录音
            </el-button>
            <el-button type="danger" @click="stopRecording" :disabled="!isRecording">
              <el-icon><VideoPause /></el-icon> 停止录音
            </el-button>
            <el-button type="primary" @click="transcribeRecording" :disabled="!hasAudioData">
              转写录音
            </el-button>
          </div>
          
          <div class="audio-info">
            <span>已录制: {{ recordedDuration }}秒</span>
            <span v-if="isRecording" class="recording-indicator">● 正在录音</span>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { transcribeApi, audioApi, configApi } from '@/api'
import { ElMessage } from 'element-plus'
import { Upload, Microphone, VideoPause } from '@element-plus/icons-vue'

const route = useRoute()
const sessionId = route.params.id
const projectId = computed(() => route.query.projectId || '')

const session = ref(null)
const audioFiles = ref([])
const loading = ref(false)
const supportedFormats = ref('.wav,.mp3,.m4a,.flac,.ogg')
const hotwords = ref('')

const isRecording = ref(false)
const hasAudioData = ref(false)
const recordedDuration = ref(0)
let ws = null
let audioBuffer = []
let recordingTimer = null

onMounted(async () => {
  await loadData()
  await loadConfig()
})

onUnmounted(() => {
  if (ws) ws.close()
  if (recordingTimer) clearInterval(recordingTimer)
})

async function loadData() {
  loading.value = true
  try {
    const res = await transcribeApi.getSessionAudioFiles(sessionId)
    audioFiles.value = res.data
  } finally {
    loading.value = false
  }
}

async function loadConfig() {
  try {
    const res = await configApi.get()
    supportedFormats.value = '.' + res.data.supported_formats.join(',')
  } catch (e) {
    console.error('Load config error:', e)
  }
}

function handleUploadSuccess(response) {
  ElMessage.success('上传成功')
  audioFiles.value.push(response)
}

function handleUploadError() {
  ElMessage.error('上传失败')
}

async function startTranscribe(audioFileId) {
  try {
    await transcribeApi.start(audioFileId, hotwords.value)
    ElMessage.success('转写任务已开始')
    await loadData()
    pollStatus(audioFileId)
  } catch (e) {
    ElMessage.error('转写失败: ' + e.message)
  }
}

async function pollStatus(audioFileId) {
  const interval = setInterval(async () => {
    const res = await transcribeApi.getAudioFile(audioFileId)
    const status = res.data.status
    
    if (status === 'completed') {
      clearInterval(interval)
      ElMessage.success('转写完成')
      await loadData()
    } else if (status === 'failed') {
      clearInterval(interval)
      ElMessage.error('转写失败: ' + res.data.error_message)
    }
  }, 3000)
}

function formatDuration(seconds) {
  if (!seconds) return '-'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function statusType(status) {
  const map = { pending: 'info', processing: 'warning', completed: 'success', failed: 'danger' }
  return map[status] || 'info'
}

function statusText(status) {
  const map = { pending: '待处理', processing: '处理中', completed: '已完成', failed: '失败' }
  return map[status] || status
}

function startRecording() {
  ws = new WebSocket(`ws://localhost:8000/ws/audio/${sessionId}`)
  
  ws.onopen = () => {
    isRecording.value = true
    audioBuffer = []
    recordedDuration.value = 0
    recordingTimer = setInterval(() => {
      recordedDuration.value += 0.5
    }, 500)
  }
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.type === 'audio_received') {
      hasAudioData.value = data.buffer_size > 0
    }
  }
  
  ws.onerror = (error) => {
    ElMessage.error('WebSocket连接失败')
    isRecording.value = false
  }
}

function stopRecording() {
  if (ws) {
    ws.send(JSON.stringify({ type: 'stop_capture' }))
  }
  isRecording.value = false
  if (recordingTimer) {
    clearInterval(recordingTimer)
    recordingTimer = null
  }
}

async function transcribeRecording() {
  if (!ws || !hasAudioData.value) return
  
  ws.send(JSON.stringify({ type: 'transcribe_buffer', hotwords: hotwords.value }))
}
</script>

<style scoped>
.session-detail {
  max-width: 1200px;
  margin: 0 auto;
}

.main-content {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.realtime-card {
  margin-top: 20px;
}

.realtime-controls {
  display: flex;
  gap: 10px;
}

.audio-info {
  margin-top: 15px;
  display: flex;
  gap: 20px;
}

.recording-indicator {
  color: #f56c6c;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>