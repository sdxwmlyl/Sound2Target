<template>
  <div class="transcript-view">
    <!-- 头部：发言人设置按钮 -->
    <div class="transcript-toolbar">
      <span class="toolbar-label">转写内容</span>
      <button class="settings-btn" @click="showSpeakerDialog = true" title="设置发言人名称">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
          <circle cx="12" cy="12" r="3"/>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
        </svg>
        <span>发言人设置</span>
      </button>
    </div>

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
          <span class="speaker-badge" :style="{ background: getSpeakerColor(segment.speaker_id) }">
            {{ getSpeakerName(segment.speaker_id) }}
          </span>
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

    <!-- 发言人名称设置弹窗 -->
    <Teleport to="body">
      <div v-if="showSpeakerDialog" class="dialog-overlay" @click.self="showSpeakerDialog = false">
        <div class="dialog-box">
          <div class="dialog-header">
            <h3>设置发言人名称</h3>
            <button class="dialog-close" @click="showSpeakerDialog = false">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
          <div class="dialog-body">
            <p class="dialog-hint">为每位发言人设置真实名称，设置后将显示在转写内容中。</p>
            <div v-for="sid in uniqueSpeakers" :key="sid" class="speaker-row">
              <label class="speaker-label">
                <span class="speaker-dot" :style="{ background: getSpeakerColor(sid) }"></span>
                发言人 {{ sid }}
              </label>
              <input
                class="speaker-input"
                v-model="editingNames[sid]"
                :placeholder="`发言人 ${sid}`"
                @keyup.enter="saveSpeakerNames"
              />
            </div>
            <div v-if="uniqueSpeakers.length === 0" class="no-speakers">
              暂无发言人数据
            </div>
          </div>
          <div class="dialog-footer">
            <button class="dialog-btn cancel" @click="showSpeakerDialog = false">取消</button>
            <button class="dialog-btn primary" @click="saveSpeakerNames">保存</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, reactive } from 'vue'
import { audioApi } from '@/api'
import { ElMessage } from 'element-plus'

const props = defineProps({
  audioId: Number
})

const loading = ref(false)
const segments = ref([])
const editingId = ref(null)
const editingText = ref('')
const editInput = ref(null)

// 发言人名称
const showSpeakerDialog = ref(false)
const speakerNames = reactive({})
const editingNames = reactive({})

const SPEAKER_COLORS = [
  '#007AFF', '#FF3B30', '#34C759', '#FF9500',
  '#AF52DE', '#5856D6', '#FF2D55', '#00C7BE'
]

const storageKey = computed(() => `s2t_speaker_names_${props.audioId}`)

const uniqueSpeakers = computed(() => {
  const ids = new Set(segments.value.map(s => s.speaker_id))
  return Array.from(ids).sort()
})

onMounted(async () => {
  loadSpeakerNames()
  await loadTranscript()
})

function loadSpeakerNames() {
  try {
    const saved = localStorage.getItem(storageKey.value)
    if (saved) {
      const names = JSON.parse(saved)
      Object.assign(speakerNames, names)
    }
  } catch (e) {
    console.error('Load speaker names error:', e)
  }
}

function saveSpeakerNames() {
  // Copy editing names to speaker names (filter empty)
  const names = {}
  for (const sid of uniqueSpeakers.value) {
    const name = (editingNames[sid] || '').trim()
    if (name) {
      names[sid] = name
    }
  }
  Object.keys(speakerNames).forEach(k => delete speakerNames[k])
  Object.assign(speakerNames, names)

  try {
    localStorage.setItem(storageKey.value, JSON.stringify(names))
    ElMessage.success('发言人名称已保存')
  } catch (e) {
    console.error('Save speaker names error:', e)
  }
  showSpeakerDialog.value = false
}

function getSpeakerName(speakerId) {
  return speakerNames[speakerId] || `发言人 ${speakerId}`
}

function getSpeakerColor(speakerId) {
  const idx = parseInt(speakerId) || 0
  return SPEAKER_COLORS[idx % SPEAKER_COLORS.length]
}

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

// Expose loadTranscript for parent to call
defineExpose({ loadTranscript })
</script>

<style scoped>
.transcript-view {
  padding: 8px 0;
}

.transcript-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 0.5px solid rgba(0, 0, 0, 0.06);
}

.toolbar-label {
  font-size: 13px;
  font-weight: 600;
  color: #8E8E93;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.settings-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: rgba(0, 122, 255, 0.08);
  border: none;
  border-radius: 6px;
  color: #007AFF;
  font-size: 12px;
  cursor: pointer;
  transition: background 150ms ease;
}

.settings-btn:hover {
  background: rgba(0, 122, 255, 0.15);
}

.settings-btn svg {
  width: 14px;
  height: 14px;
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
  border: 2px solid rgba(0, 0, 0, 0.1);
  border-top-color: #007AFF;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.segments-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.segment-item {
  padding: 10px 12px;
  border-radius: 8px;
  transition: background 150ms ease;
}

.segment-item:hover {
  background: rgba(0, 122, 255, 0.03);
}

.segment-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.time-badge {
  font-size: 12px;
  font-family: 'SF Mono', monospace;
  color: #8E8E93;
  background: rgba(0, 0, 0, 0.04);
  padding: 2px 6px;
  border-radius: 4px;
}

.speaker-badge {
  font-size: 12px;
  font-weight: 500;
  color: #fff;
  padding: 2px 8px;
  border-radius: 4px;
}

.segment-text {
  font-size: 15px;
  line-height: 1.6;
  color: #1C1C1E;
  cursor: text;
  position: relative;
  padding-right: 20px;
}

.segment-text:hover {
  color: #007AFF;
}

.edited-icon {
  position: absolute;
  right: 0;
  top: 2px;
  color: #8E8E93;
}

textarea {
  width: 100%;
  min-height: 60px;
  padding: 8px;
  border: 1px solid #007AFF;
  border-radius: 6px;
  font-size: 15px;
  line-height: 1.6;
  resize: vertical;
  outline: none;
  font-family: inherit;
}

.empty {
  text-align: center;
  padding: 40px 20px;
  color: #8E8E93;
}

/* ===== Speaker Dialog ===== */
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
}

.dialog-box {
  background: #fff;
  border-radius: 14px;
  width: 420px;
  max-width: 90vw;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 0.5px solid rgba(0, 0, 0, 0.1);
}

.dialog-header h3 {
  font-size: 17px;
  font-weight: 600;
  color: #1C1C1E;
  margin: 0;
}

.dialog-close {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  color: #8E8E93;
  border-radius: 6px;
}

.dialog-close:hover {
  background: rgba(0, 0, 0, 0.05);
}

.dialog-close svg {
  width: 20px;
  height: 20px;
}

.dialog-body {
  padding: 16px 20px;
}

.dialog-hint {
  font-size: 13px;
  color: #8E8E93;
  margin: 0 0 16px 0;
}

.speaker-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.speaker-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #3C3C43;
  min-width: 100px;
  font-weight: 500;
}

.speaker-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.speaker-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: border-color 200ms ease;
}

.speaker-input:focus {
  border-color: #007AFF;
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
}

.no-speakers {
  text-align: center;
  padding: 20px;
  color: #8E8E93;
  font-size: 14px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 20px;
  border-top: 0.5px solid rgba(0, 0, 0, 0.1);
}

.dialog-btn {
  padding: 8px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 150ms ease;
}

.dialog-btn.cancel {
  background: rgba(0, 0, 0, 0.05);
  color: #3C3C43;
}

.dialog-btn.cancel:hover {
  background: rgba(0, 0, 0, 0.1);
}

.dialog-btn.primary {
  background: #007AFF;
  color: #fff;
}

.dialog-btn.primary:hover {
  background: #0056CC;
}
</style>
