<template>
  <div class="realtime-recorder">
    <div class="recorder-overlay" @click.self="$emit('close')">
      <div class="recorder-dialog">
        <div class="recorder-header">
          <h3>{{ sourceType === 'microphone' ? '外部录音' : '系统录音' }}</h3>
          <button class="close-btn" @click="$emit('close')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        
        <div class="recorder-body">
          <div class="recorder-status">
            <div class="status-icon" :class="{ recording: isRecording }">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
              </svg>
            </div>
            <div class="status-text">
              <span v-if="!isRecording">准备开始录音</span>
              <span v-else>录音中... {{ formatDuration(recordingDuration) }}</span>
            </div>
            <div class="status-indicator" v-if="isRecording">
              <span class="dot"></span>
              <span>实时转写中</span>
            </div>
          </div>
          
          <!-- 实时转写结果 -->
          <div class="realtime-text" v-if="realtimeSegments.length > 0">
            <div 
              v-for="(seg, i) in realtimeSegments" 
              :key="i"
              class="text-item"
            >
              <span class="text-speaker">发言人{{ seg.speaker_id }}</span>
              <span class="text-content">{{ seg.text }}</span>
            </div>
          </div>
        </div>
        
        <div class="recorder-footer">
          <button 
            v-if="!isRecording" 
            class="btn-start" 
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
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  projectId: String,
  sourceType: String,
  audioName: String
})

const emit = defineEmits(['close', 'complete'])

const isRecording = ref(false)
const recordingDuration = ref(0)
const realtimeSegments = ref([])
let ws = null
let durationTimer = null
let sessionId = `session_${Date.now()}`

onUnmounted(() => {
  cleanup()
})

function startRecording() {
  ws = new WebSocket(`ws://localhost:8000/api/realtime/ws/${props.projectId}?session_id=${sessionId}`)
  
  ws.onopen = () => {
    ws.send(JSON.stringify({
      type: 'start_recording',
      source_type: props.sourceType,
      hotwords: '',
      audio_name: props.audioName
    }))
    
    isRecording.value = true
    recordingDuration.value = 0
    durationTimer = setInterval(() => {
      recordingDuration.value++
    }, 1000)
  }
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    handleWsMessage(data)
  }
  
  ws.onerror = (error) => {
    ElMessage.error('WebSocket连接失败')
    console.error('WebSocket error:', error)
    cleanup()
  }
  
  ws.onclose = () => {
    if (isRecording.value) {
      ElMessage.warning('连接已断开')
      cleanup()
    }
  }
}

function stopRecording() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'stop_recording' }))
  }
  
  setTimeout(() => {
    cleanup()
    emit('complete')
  }, 1000)
}

function handleWsMessage(data) {
  switch (data.type) {
    case 'recording_started':
      ElMessage.success('录音已开始')
      break
    
    case 'realtime_result':
      if (data.segments) {
        realtimeSegments.value.push(...data.segments)
      }
      break
    
    case 'recording_stopped':
      ElMessage.success('录音已停止')
      break
    
    case 'error':
      ElMessage.error(data.message)
      break
  }
}

function cleanup() {
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

function formatDuration(seconds) {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.recorder-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.recorder-dialog {
  width: 500px;
  background: white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.recorder-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 0.5px solid rgba(0, 0, 0, 0.1);
}

.recorder-header h3 {
  font-size: 17px;
  font-weight: 600;
  color: #1C1C1E;
  margin: 0;
}

.close-btn {
  width: 28px;
  height: 28px;
  background: rgba(142, 142, 147, 0.12);
  border: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #3C3C43;
}

.close-btn svg {
  width: 16px;
  height: 16px;
}

.recorder-body {
  padding: 24px 20px;
}

.recorder-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.status-icon {
  width: 64px;
  height: 64px;
  background: #F2F2F7;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8E8E93;
}

.status-icon.recording {
  background: rgba(255, 59, 48, 0.1);
  color: #FF3B30;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.status-icon svg {
  width: 28px;
  height: 28px;
}

.status-text {
  font-size: 17px;
  font-weight: 500;
  color: #1C1C1E;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #FF3B30;
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
  max-height: 200px;
  overflow-y: auto;
  padding: 12px;
  background: #F2F2F7;
  border-radius: 10px;
}

.text-item {
  display: flex;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 0.5px solid rgba(0, 0, 0, 0.06);
}

.text-item:last-child {
  border-bottom: none;
}

.text-speaker {
  font-size: 12px;
  color: #8E8E93;
  min-width: 60px;
}

.text-content {
  font-size: 14px;
  color: #1C1C1E;
  line-height: 1.4;
}

.recorder-footer {
  padding: 16px 20px;
  border-top: 0.5px solid rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: center;
}

.btn-start {
  padding: 12px 40px;
  background: #34C759;
  border: none;
  border-radius: 10px;
  font-size: 17px;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: background 150ms ease;
}

.btn-start:hover {
  background: #2DB84E;
}

.btn-stop {
  padding: 12px 40px;
  background: #FF3B30;
  border: none;
  border-radius: 10px;
  font-size: 17px;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: background 150ms ease;
}

.btn-stop:hover {
  background: #E5352B;
}
</style>