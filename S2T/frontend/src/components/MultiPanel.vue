<template>
  <div class="multi-panel">
    <!-- 默认状态：转写内容列表 -->
    <div v-if="mode === 'default'" class="panel-default">
      <div class="panel-header">
        <h3>转写内容</h3>
        <span class="content-count">{{ audioFiles.length }} 个文件</span>
      </div>
      
      <div class="content-list">
        <div 
          v-for="audio in completedFiles" 
          :key="audio.id" 
          class="content-card"
          :class="{ expanded: expandedId === audio.id }"
        >
          <div class="card-header" @click="toggleExpand(audio.id)">
            <div class="card-info">
              <span class="card-name">{{ audio.audio_name }}</span>
              <span class="card-meta">{{ getTypeLabel(audio.source_type) }} · {{ formatTime(audio.created_at) }}</span>
            </div>
            <div class="card-stats">
              <span class="char-count">{{ audio.char_count || 0 }} 字</span>
              <svg 
                class="expand-icon" 
                :class="{ rotated: expandedId === audio.id }"
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                stroke-width="2"
              >
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </div>
          </div>
          
          <div v-if="expandedId === audio.id" class="card-content">
            <TranscriptView :audio-id="audio.id" />
          </div>
        </div>
        
        <div v-if="completedFiles.length === 0" class="empty-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="40" height="40">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
          </svg>
          <p>暂无转写内容</p>
        </div>
      </div>
    </div>
    
    <!-- 对照回顾状态 -->
    <PlaybackReview 
      v-if="mode === 'playback' && selectedAudio"
      :audio="selectedAudio"
      @close="$emit('close')"
    />
    
    <!-- AI问答状态 -->
    <AIChat 
      v-if="mode === 'ai-chat'"
      :project-id="projectId"
      @close="$emit('close')"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import TranscriptView from './TranscriptView.vue'
import PlaybackReview from './PlaybackReview.vue'
import AIChat from './AIChat.vue'

const props = defineProps({
  mode: String,
  audioFiles: Array,
  selectedAudio: Object,
  projectId: String
})

const emit = defineEmits(['close', 'play'])

const expandedId = ref(null)

const completedFiles = computed(() => {
  return props.audioFiles.filter(a => a.status === 'completed')
})

function toggleExpand(id) {
  expandedId.value = expandedId.value === id ? null : id
}

function getTypeLabel(type) {
  const labels = { file: '文件', microphone: '麦克风', system: '系统' }
  return labels[type] || type
}

function formatTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.multi-panel {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 16px;
  border: 0.5px solid rgba(0, 0, 0, 0.1);
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-default {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 0.5px solid rgba(0, 0, 0, 0.1);
}

.panel-header h3 {
  font-size: 17px;
  font-weight: 600;
  color: #1C1C1E;
  margin: 0;
}

.content-count {
  font-size: 13px;
  color: #8E8E93;
}

.content-list {
  max-height: 600px;
  overflow-y: auto;
}

.content-card {
  border-bottom: 0.5px solid rgba(0, 0, 0, 0.06);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  cursor: pointer;
  transition: background 150ms ease;
}

.card-header:hover {
  background: rgba(0, 122, 255, 0.05);
}

.card-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.card-name {
  font-size: 15px;
  font-weight: 500;
  color: #1C1C1E;
}

.card-meta {
  font-size: 13px;
  color: #8E8E93;
}

.card-stats {
  display: flex;
  align-items: center;
  gap: 8px;
}

.char-count {
  font-size: 13px;
  color: #8E8E93;
}

.expand-icon {
  width: 20px;
  height: 20px;
  color: #8E8E93;
  transition: transform 200ms ease;
}

.expand-icon.rotated {
  transform: rotate(180deg);
}

.card-content {
  padding: 0 20px 16px;
  max-height: 300px;
  overflow-y: auto;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #8E8E93;
}

.empty-state svg {
  color: #AEAEB2;
  margin-bottom: 12px;
}

.empty-state p {
  font-size: 15px;
  margin: 0;
}
</style>