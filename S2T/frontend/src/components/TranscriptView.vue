<template>
  <div class="transcript-view">
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <span>加载中...</span>
    </div>
    
    <div v-else-if="segments.length > 0" class="segments-list">
      <div 
        v-for="segment in segments" 
        :key="segment.id" 
        class="segment-item"
      >
        <div class="segment-header">
          <span class="time-badge">{{ formatTime(segment.start_time) }} - {{ formatTime(segment.end_time) }}</span>
          <span class="speaker-badge">发言人 {{ segment.speaker_id }}</span>
        </div>
        <div class="segment-text" @click="startEdit(segment)">
          <template v-if="editingId === segment.id">
            <textarea 
              v-model="editingText" 
              @blur="saveEdit(segment.id)"
              @keyup.ctrl.enter="saveEdit(segment.id)"
              ref="editInput"
            ></textarea>
          </template>
          <template v-else>
            {{ segment.text }}
            <svg v-if="segment.edited" class="edited-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
          </template>
        </div>
      </div>
    </div>
    
    <div v-else class="empty">
      <p>暂无转写内容</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { audioApi } from '@/api'

const props = defineProps({
  audioId: Number
})

const loading = ref(false)
const segments = ref([])
const editingId = ref(null)
const editingText = ref('')
const editInput = ref(null)

onMounted(async () => {
  await loadTranscript()
})

async function loadTranscript() {
  loading.value = true
  try {
    const res = await audioApi.getTranscript(props.audioId)
    segments.value = res.data.segments
  } catch (e) {
    console.error('Load transcript error:', e)
  } finally {
    loading.value = false
  }
}

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

function startEdit(segment) {
  editingId.value = segment.id
  editingText.value = segment.text
  nextTick(() => {
    if (editInput.value) {
      editInput.value.focus()
    }
  })
}

async function saveEdit(segmentId) {
  if (editingText.value.trim()) {
    try {
      await audioApi.updateSegment(segmentId, editingText.value)
      await loadTranscript()
    } catch (e) {
      console.error('Save edit error:', e)
    }
  }
  editingId.value = null
  editingText.value = ''
}
</script>

<style scoped>
.transcript-view {
  padding: 8px 0;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  color: #8E8E93;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #E5E5EA;
  border-top-color: #007AFF;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.segments-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.segment-item {
  padding: 10px 12px;
  background: #F2F2F7;
  border-radius: 10px;
}

.segment-header {
  display: flex;
  gap: 8px;
  margin-bottom: 6px;
}

.time-badge {
  padding: 2px 6px;
  background: rgba(0, 122, 255, 0.1);
  color: #007AFF;
  font-size: 11px;
  font-weight: 500;
  border-radius: 4px;
}

.speaker-badge {
  font-size: 11px;
  color: #8E8E93;
}

.segment-text {
  font-size: 14px;
  line-height: 1.5;
  color: #1C1C1E;
  cursor: pointer;
  position: relative;
}

.segment-text:hover {
  background: rgba(0, 122, 255, 0.05);
  border-radius: 6px;
}

.segment-text textarea {
  width: 100%;
  padding: 6px;
  font-size: 14px;
  line-height: 1.5;
  border: 1px solid #007AFF;
  border-radius: 6px;
  resize: vertical;
  font-family: inherit;
}

.segment-text textarea:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.15);
}

.edited-icon {
  color: #FF9500;
  margin-left: 4px;
  vertical-align: middle;
}

.empty {
  padding: 20px;
  text-align: center;
  color: #8E8E93;
}

.empty p {
  margin: 0;
}
</style>