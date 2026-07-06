<template>
  <div class="realtime-capture">
    <el-card>
      <template #header>
        <span>实时录音</span>
      </template>
      
      <div class="source-select">
        <el-radio-group v-model="sourceType" :disabled="isRecording">
          <el-radio-button value="microphone">麦克风</el-radio-button>
          <el-radio-button value="system">系统声音</el-radio-button>
        </el-radio-group>
      </div>
      
      <div class="hotwords-input">
        <el-input
          v-model="hotwords"
          placeholder="热词配置（可选）"
          :disabled="isRecording"
          size="small"
        />
      </div>
      
      <div class="controls">
        <el-button
          type="success"
          size="large"
          @click="startRecording"
          :disabled="isRecording"
        >
          <el-icon><Microphone /></el-icon>
          开始录音
        </el-button>
        
        <el-button
          type="danger"
          size="large"
          @click="stopRecording"
          :disabled="!isRecording"
        >
          <el-icon><VideoPause /></el-icon>
          停止录音
        </el-button>
      </div>
      
      <div class="recording-status" v-if="isRecording">
        <el-progress :percentage="bufferProgress" :indeterminate="true" />
        <div class="status-info">
          <span class="recording-indicator">● 正在录音</span>
          <span>已录制: {{ bufferDuration.toFixed(1) }}秒</span>
        </div>
      </div>
      
      <div class="realtime-results" v-if="segments.length > 0">
        <el-divider>实时转写结果</el-divider>
        <div class="segment-list">
          <div v-for="(seg, i) in segments" :key="i" class="segment">
            <el-tag size="small" type="info">发言人{{ seg.speaker_id }}</el-tag>
            <span class="text">{{ seg.text }}</span>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Microphone, VideoPause } from '@element-plus/icons-vue'

const props = defineProps({
  sessionId: String
})

const emit = defineEmits(['transcribe-complete'])

const sourceType = ref('microphone')
const hotwords = ref('')
const isRecording = ref(false)
const bufferDuration = ref(0)
const segments = ref([])

const bufferProgress = computed(() => Math.min(bufferDuration.value / 30 * 100, 100))

let ws = null
let mediaStream = null
let audioContext = null
let audioWorklet = null
let wsReconnectTimer = null

onMounted(() => {
  initAudioDevices()
})

onUnmounted(() => {
  cleanup()
})

async function initAudioDevices() {
  try {
    if (navigator.mediaDevices) {
      const devices = await navigator.mediaDevices.enumerateDevices()
      console.log('Audio devices:', devices.filter(d => d.kind === 'audioinput'))
    }
  }
  catch (e) {
    console.error('Get devices error:', e)
  }
}

function connectWebSocket() {
  ws = new WebSocket(`ws://localhost:8000/api/realtime/ws/${props.sessionId}`)
  
  ws.onopen = async () => {
    ws.send(JSON.stringify({
      type: 'set_hotwords',
      hotwords: hotwords.value
    }))
    
    ws.send(JSON.stringify({
      type: 'start_recording',
      source_type: sourceType.value,
      hotwords: hotwords.value
    }))
    
    await startAudioCapture()
    
    isRecording.value = true
    ElMessage.success('开始录音')
  }
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    handleMessage(data)
  }
  
  ws.onerror = (error) => {
    ElMessage.error('WebSocket连接失败')
    cleanup()
  }
  
  ws.onclose = () => {
    if (isRecording.value) {
      wsReconnectTimer = setTimeout(() => {
        if (isRecording.value) connectWebSocket()
      }, 3000)
    }
  }
}

function handleMessage(data) {
  switch (data.type) {
    case 'realtime_result':
      segments.value.push(...(data.segments || []))
      break
    
    case 'final_result':
      segments.value.push(...(data.segments || []))
      emit('transcribe-complete', data)
      break
    
    case 'audio_received':
      bufferDuration.value = data.buffer_duration || 0
      break
    
    case 'error':
      ElMessage.error(data.message)
      break
  }
}

async function startRecording() {
  segments.value = []
  bufferDuration.value = 0
  
  connectWebSocket()
}

async function startAudioCapture() {
  try {
    audioContext = new AudioContext({ sampleRate: 16000 })
    
    const constraints = {
      audio: sourceType.value === 'microphone' 
        ? { echoCancellation: true, noiseSuppression: true }
        : { echoCancellation: false }
    }
    
    mediaStream = await navigator.mediaDevices.getUserMedia(constraints)
    
    const source = audioContext.createMediaStreamSource(mediaStream)
    
    await audioContext.audioWorklet.addModule('/audio-processor.js')
    audioWorklet = new AudioWorkletNode(audioContext, 'audio-processor')
    
    source.connect(audioWorklet)
    
    audioWorklet.port.onmessage = (event) => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        const audioData = event.data
        const base64 = btoa(String.fromCharCode(...new Uint8Array(audioData)))
        ws.send(JSON.stringify({
          type: 'audio_data',
          audio_data: base64
        }))
      }
    }
    
  }
  catch (e) {
    ElMessage.error('无法启动音频捕获: ' + e.message)
    cleanup()
  }
}

function stopRecording() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'stop_recording' }))
  }
  
  cleanup()
  
  isRecording.value = false
  ElMessage.success('录音已停止')
}

function cleanup() {
  if (wsReconnectTimer) {
    clearTimeout(wsReconnectTimer)
    wsReconnectTimer = null
  }
  
  if (ws) {
    ws.close()
    ws = null
  }
  
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop())
    mediaStream = null
  }
  
  if (audioContext) {
    audioContext.close()
    audioContext = null
  }
}

defineExpose({ startRecording, stopRecording })
</script>

<style scoped>
.realtime-capture {
  max-width: 600px;
}

.source-select {
  margin-bottom: 15px;
}

.hotwords-input {
  margin-bottom: 15px;
}

.controls {
  display: flex;
  gap: 20px;
  justify-content: center;
  margin: 20px 0;
}

.recording-status {
  margin: 20px 0;
}

.status-info {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
}

.recording-indicator {
  color: #f56c6c;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.realtime-results {
  margin-top: 20px;
}

.segment-list {
  max-height: 300px;
  overflow-y: auto;
}

.segment {
  padding: 8px;
  margin: 5px 0;
  background: #f5f7fa;
  border-radius: 4px;
}

.segment .text {
  margin-left: 10px;
}
</style>