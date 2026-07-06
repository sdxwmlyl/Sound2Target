<template>
  <div class="transcript-editor">
    <!-- Header with back button -->
    <div class="page-header">
      <button class="back-btn" @click="goBack">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
        <span>返回</span>
      </button>
      <h1 class="page-title">{{ audioFile?.filename || '转写结果' }}</h1>
      <div class="header-actions">
        <button class="btn-secondary" @click="exportTranscript">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          <span>导出</span>
        </button>
      </div>
    </div>
    
    <!-- Main content -->
    <div class="editor-grid">
      <!-- Transcript panel -->
      <div class="transcript-panel">
        <div class="panel-header">
          <h3>转写内容</h3>
          <div class="stats-row">
            <span class="stat">{{ segments.length }} 个段落</span>
            <span class="stat">{{ getSpeakerCount() }} 位发言人</span>
          </div>
        </div>
        
        <div class="segments-list" v-loading="loading">
          <div 
            v-for="segment in segments" 
            :key="segment.id"
            class="segment-item"
            :class="{ edited: segment.edited }"
          >
            <div class="segment-header">
              <span class="time-badge">{{ formatTime(segment.start_time) }} - {{ formatTime(segment.end_time) }}</span>
              <span class="speaker-badge">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
                发言人 {{ segment.speaker_id }}
              </span>
              <span v-if="segment.edited" class="edited-badge">已编辑</span>
            </div>
            <div class="segment-text">
              <div v-if="editingId === segment.id" class="edit-mode">
                <textarea v-model="editingText" rows="3" @keyup.ctrl.enter="saveEdit(segment.id)"></textarea>
                <div class="edit-actions">
                  <button class="btn-sm-primary" @click="saveEdit(segment.id)">保存</button>
                  <button class="btn-sm-secondary" @click="cancelEdit">取消</button>
                </div>
              </div>
              <div v-else class="text-display" @click="startEdit(segment)">
                {{ segment.text }}
                <button class="edit-btn" title="点击编辑">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- AI panel -->
      <div class="ai-panel">
        <!-- Summary section -->
        <div class="ai-section">
          <div class="section-header">
            <h3>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
              </svg>
              AI总结
            </h3>
          </div>
          
          <div class="prompt-input">
            <textarea 
              v-model="summaryPrompt" 
              rows="3" 
              placeholder="输入总结要求，如：提取会议主题、关键决议..."
            ></textarea>
          </div>
          
          <button class="btn-primary full-width" @click="generateSummary" :disabled="summaryLoading">
            <svg v-if="!summaryLoading" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
            </svg>
            <span v-if="summaryLoading">正在生成...</span>
            <span v-else>生成会议纪要</span>
          </button>
          
          <div v-if="summary" class="summary-output">
            <div class="output-header">
              <span class="output-label">生成的纪要</span>
              <button class="btn-icon-sm" @click="copySummary">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                </svg>
              </button>
            </div>
            <div class="output-content">{{ summary }}</div>
          </div>
        </div>
        
        <!-- Chat section -->
        <div class="ai-section">
          <div class="section-header">
            <h3>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
              智能问答
            </h3>
          </div>
          
          <div class="chat-messages">
            <div v-for="(msg, i) in chatHistory" :key="i" :class="['chat-message', msg.role]">
              <div class="message-avatar">
                <svg v-if="msg.role === 'user'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
                  <line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
              </div>
              <div class="message-content">{{ msg.content }}</div>
            </div>
          </div>
          
          <div class="chat-input">
            <input 
              v-model="chatQuestion" 
              placeholder="输入问题，如：会议中讨论了哪些议题？" 
              @keyup.enter="sendQuestion"
            />
            <button class="btn-send" @click="sendQuestion" :disabled="chatLoading">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { transcribeApi, llmApi } from '@/api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const audioId = route.params.audioId

const audioFile = ref(null)
const segments = ref([])
const loading = ref(false)

const editingId = ref(null)
const editingText = ref('')

const summary = ref('')
const summaryPrompt = ref('- 会议主题是什么？\n- 罗列每个发言人的核心观点\n- 整理决议事项和后续待办')
const summaryLoading = ref(false)

const chatHistory = ref([])
const chatQuestion = ref('')
const chatLoading = ref(false)

onMounted(async () => {
  await loadData()
})

async function loadData() {
  loading.value = true
  try {
    const res = await transcribeApi.getTranscript(audioId)
    audioFile.value = res.data.audio_file
    segments.value = res.data.segments
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.back()
}

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

function getSpeakerCount() {
  return new Set(segments.value.map(s => s.speaker_id)).size
}

function startEdit(segment) {
  editingId.value = segment.id
  editingText.value = segment.text
}

function cancelEdit() {
  editingId.value = null
  editingText.value = ''
}

async function saveEdit(segmentId) {
  if (editingText.value.trim()) {
    await transcribeApi.updateSegment(segmentId, editingText.value)
    await loadData()
    ElMessage.success('已保存修改')
  }
  cancelEdit()
}

async function generateSummary() {
  summaryLoading.value = true
  try {
    const res = await llmApi.summarize(audioId, summaryPrompt.value)
    summary.value = res.data.summary
  } catch (e) {
    ElMessage.error('生成失败: ' + e.message)
  } finally {
    summaryLoading.value = false
  }
}

async function sendQuestion() {
  if (!chatQuestion.value.trim()) return
  
  chatLoading.value = true
  try {
    const res = await llmApi.chat(audioId, chatQuestion.value, chatHistory.value)
    
    chatHistory.value.push({ role: 'user', content: chatQuestion.value })
    chatHistory.value.push({ role: 'assistant', content: res.data.answer })
    
    chatQuestion.value = ''
  } catch (e) {
    ElMessage.error('问答失败: ' + e.message)
  } finally {
    chatLoading.value = false
  }
}

function copySummary() {
  navigator.clipboard.writeText(summary.value)
  ElMessage.success('已复制到剪贴板')
}

function exportTranscript() {
  const text = segments.value
    .map(s => `[${formatTime(s.start_time)}-${formatTime(s.end_time)}] 发言人${s.speaker_id}: ${s.text}`)
    .join('\n\n')
  
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${audioFile.value?.filename || 'transcript'}.txt`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.transcript-editor {
  max-width: 1400px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  background: transparent;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  color: #64748b;
  font-size: 14px;
  cursor: pointer;
  transition: all 150ms ease;
}

.back-btn:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.back-btn svg {
  width: 18px;
  height: 18px;
}

.page-title {
  flex: 1;
  font-size: 20px;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.btn-secondary {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  color: #0f172a;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 150ms ease;
}

.btn-secondary:hover {
  background: #e2e8f0;
}

.btn-secondary svg {
  width: 18px;
  height: 18px;
}

.btn-primary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 20px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 150ms ease;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary.full-width {
  width: 100%;
}

.editor-grid {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 24px;
}

.transcript-panel, .ai-panel {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
}

.panel-header {
  padding: 20px;
  border-bottom: 1px solid #e2e8f0;
}

.panel-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 12px 0;
}

.stats-row {
  display: flex;
  gap: 16px;
}

.stat {
  font-size: 13px;
  color: #64748b;
}

.segments-list {
  max-height: 600px;
  overflow-y: auto;
  padding: 16px;
}

.segment-item {
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  margin-bottom: 12px;
  transition: background 150ms ease;
}

.segment-item:hover {
  background: #f1f5f9;
}

.segment-item.edited {
  background: rgba(245, 158, 11, 0.05);
  border-left: 3px solid #f59e0b;
}

.segment-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.time-badge {
  padding: 4px 8px;
  background: rgba(99, 102, 241, 0.1);
  color: #6366f1;
  font-size: 12px;
  font-weight: 500;
  border-radius: 4px;
}

.speaker-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #64748b;
}

.edited-badge {
  padding: 2px 6px;
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
  font-size: 11px;
  border-radius: 4px;
}

.text-display {
  font-size: 14px;
  line-height: 1.6;
  color: #0f172a;
  cursor: pointer;
  position: relative;
}

.edit-btn {
  position: absolute;
  right: 0;
  top: 0;
  opacity: 0;
  transition: opacity 150ms ease;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  padding: 4px;
  cursor: pointer;
}

.text-display:hover .edit-btn {
  opacity: 1;
}

.edit-btn svg {
  width: 14px;
  height: 14px;
  color: #64748b;
}

.edit-mode textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #2563eb;
  border-radius: 6px;
  font-size: 14px;
  resize: vertical;
}

.edit-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.btn-sm-primary {
  padding: 6px 12px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
}

.btn-sm-secondary {
  padding: 6px 12px;
  background: #f1f5f9;
  color: #64748b;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
}

.ai-section {
  padding: 20px;
  border-bottom: 1px solid #e2e8f0;
}

.ai-section:last-child {
  border-bottom: none;
}

.section-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 16px 0;
}

.section-header svg {
  color: #6366f1;
}

.prompt-input textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 13px;
  resize: vertical;
  margin-bottom: 12px;
}

.summary-output {
  margin-top: 16px;
  background: #f8fafc;
  border-radius: 8px;
  padding: 16px;
}

.output-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.output-label {
  font-size: 12px;
  font-weight: 500;
  color: #64748b;
}

.btn-icon-sm {
  padding: 4px;
  background: transparent;
  border: none;
  cursor: pointer;
  color: #64748b;
}

.btn-icon-sm:hover {
  color: #2563eb;
}

.btn-icon-sm svg {
  width: 16px;
  height: 16px;
}

.output-content {
  font-size: 14px;
  line-height: 1.6;
  color: #0f172a;
  white-space: pre-wrap;
}

.chat-messages {
  max-height: 200px;
  overflow-y: auto;
  margin-bottom: 12px;
}

.chat-message {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.message-avatar {
  width: 28px;
  height: 28px;
  background: #f1f5f9;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.message-avatar svg {
  width: 16px;
  height: 16px;
  color: #64748b;
}

.chat-message.assistant .message-avatar {
  background: rgba(99, 102, 241, 0.1);
}

.chat-message.assistant .message-avatar svg {
  color: #6366f1;
}

.message-content {
  flex: 1;
  font-size: 13px;
  line-height: 1.5;
  color: #0f172a;
  padding: 6px 10px;
  background: #f8fafc;
  border-radius: 6px;
}

.chat-message.assistant .message-content {
  background: rgba(99, 102, 241, 0.05);
}

.chat-input {
  display: flex;
  gap: 8px;
}

.chat-input input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 13px;
}

.chat-input input:focus {
  outline: none;
  border-color: #2563eb;
}

.btn-send {
  padding: 10px;
  background: #2563eb;
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
  transition: background 150ms ease;
}

.btn-send:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-send:disabled {
  opacity: 0.6;
}

.btn-send svg {
  width: 18px;
  height: 18px;
}

@media (max-width: 1024px) {
  .editor-grid {
    grid-template-columns: 1fr;
  }
}
</style>