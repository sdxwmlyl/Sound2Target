<template>
  <div class="playback-review">
    <!-- 固定区域：播放控制 + AI总结 -->
    <div class="fixed-section">
      <!-- 顶部：播放控制 -->
      <div class="playback-header">
        <div class="header-top">
          <h3>{{ audio.audio_name }}</h3>
          <button class="close-btn" @click="$emit('close')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        
        <div class="player-controls">
          <button class="play-btn" @click="togglePlay">
            <svg v-if="!isPlaying" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="5 3 19 12 5 21 5 3"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="6" y="4" width="4" height="16"/>
              <rect x="14" y="4" width="4" height="16"/>
            </svg>
          </button>
          
          <div class="progress-container">
            <span class="time">{{ formatTime(currentTime) }}</span>
            <div class="progress-bar" @click="seek">
              <div class="progress-fill" :style="{ width: progress + '%' }"></div>
              <div class="progress-handle" :style="{ left: progress + '%' }"></div>
            </div>
            <span class="time">{{ formatTime(duration) }}</span>
          </div>
        </div>
      </div>
      
      <!-- AI总结 -->
      <div class="summary-section">
        <div class="section-header">
          <h4>AI总结</h4>
          <button class="summarize-btn" @click="generateSummary" :disabled="summaryLoading">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
            </svg>
            <span>{{ summaryLoading ? '生成中...' : '一键总结' }}</span>
          </button>
        </div>
        <div class="summary-content markdown-body" v-if="summary" v-html="summaryHtml"></div>
        <div class="summary-empty" v-else>
          <p>点击"一键总结"生成内容摘要</p>
        </div>
      </div>
    </div>
    
    <!-- 滚动区域：字幕 -->
    <div class="scrollable-section" ref="subtitleContainer">
      <div 
        v-for="segment in segments" 
        :key="segment.id"
        class="subtitle-item"
        :class="{ active: isActiveSegment(segment) }"
        :ref="el => { if (isActiveSegment(segment)) activeSegmentEl = el }"
        @click="seekToSegment(segment)"
      >
        <span class="subtitle-time">{{ formatTime(segment.start_time) }}</span>
        <span class="subtitle-speaker" :style="{ background: getSpeakerColor(segment.speaker_id) }">{{ getSpeakerName(segment.speaker_id) }}</span>
        <span class="subtitle-text">{{ segment.text }}</span>
      </div>
    </div>
    
    <!-- 音频元素 -->
    <audio 
      ref="audioPlayer" 
      :src="audioUrl" 
      @timeupdate="onTimeUpdate"
      @loadedmetadata="onMetadataLoaded"
      @ended="isPlaying = false"
      @error="onAudioError"
    ></audio>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, watch, nextTick } from 'vue'
import { audioApi, llmApi } from '@/api'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'

const props = defineProps({
  audio: Object
})

const emit = defineEmits(['close'])

const audioPlayer = ref(null)
const subtitleContainer = ref(null)
const activeSegmentEl = ref(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const segments = ref([])
const summary = ref('')
const summaryLoading = ref(false)

// Speaker names from localStorage
const speakerNames = reactive({})
const SPEAKER_COLORS = [
  '#007AFF', '#FF3B30', '#34C759', '#FF9500',
  '#AF52DE', '#5856D6', '#FF2D55', '#00C7BE'
]

function loadSpeakerNames() {
  try {
    const key = `s2t_speaker_names_${props.audio.id}`
    const saved = localStorage.getItem(key)
    if (saved) Object.assign(speakerNames, JSON.parse(saved))
  } catch (e) { /* ignore */ }
}

function getSpeakerName(speakerId) {
  return speakerNames[speakerId] || `发言人 ${speakerId}`
}

function getSpeakerColor(speakerId) {
  const idx = parseInt(speakerId) || 0
  return SPEAKER_COLORS[idx % SPEAKER_COLORS.length]
}

// 音频文件URL - 使用正确的API路径
const audioUrl = computed(() => {
  return `/api/audio-files/${props.audio.id}/stream`
})

const summaryHtml = computed(() => {
  return summary.value ? marked(summary.value) : ''
})

const progress = computed(() => {
  if (!duration.value) return 0
  return (currentTime.value / duration.value) * 100
})

// 监听audio属性变化，重新加载数据
watch(() => props.audio, async (newAudio) => {
  if (newAudio) {
    loadSpeakerNames()
    await loadTranscript()
    resetPlayer()
  }
}, { immediate: true })

onMounted(async () => {
  loadSpeakerNames()
  await loadTranscript()
})

function resetPlayer() {
  isPlaying.value = false
  currentTime.value = 0
  duration.value = 0
  summary.value = ''
}

async function loadTranscript() {
  try {
    const res = await audioApi.getTranscript(props.audio.id)
    segments.value = res.data.segments
    
    // 加载已保存的总结
    if (res.data.audio_file && res.data.audio_file.summary) {
      summary.value = res.data.audio_file.summary
    } else {
      summary.value = ''
    }
  } catch (e) {
    console.error('Load transcript error:', e)
  }
}

function togglePlay() {
  if (audioPlayer.value) {
    if (isPlaying.value) {
      audioPlayer.value.pause()
    } else {
      audioPlayer.value.play().catch(e => {
        console.error('Play error:', e)
        ElMessage.error('音频加载失败')
      })
    }
    isPlaying.value = !isPlaying.value
  }
}

function seek(e) {
  if (audioPlayer.value && duration.value) {
    const rect = e.currentTarget.getBoundingClientRect()
    const x = e.clientX - rect.left
    const percent = x / rect.width
    audioPlayer.value.currentTime = percent * duration.value
  }
}

function seekToSegment(segment) {
  console.log('Seeking to:', segment.start_time)
  if (audioPlayer.value) {
    // 先暂停播放，避免onTimeUpdate事件覆盖currentTime
    const wasPlaying = isPlaying.value
    if (wasPlaying) {
      audioPlayer.value.pause()
    }
    
    // 设置currentTime
    audioPlayer.value.currentTime = segment.start_time
    currentTime.value = segment.start_time
    
    // 恢复播放
    if (wasPlaying) {
      setTimeout(() => {
        audioPlayer.value.play().catch(e => console.error('Play error:', e))
      }, 50)
    } else {
      audioPlayer.value.play().catch(e => console.error('Play error:', e))
      isPlaying.value = true
    }
  } else {
    console.error('Audio player not found')
  }
}

function onTimeUpdate() {
  if (audioPlayer.value) {
    currentTime.value = audioPlayer.value.currentTime
    scrollToActiveSegment()
  }
}

function onMetadataLoaded() {
  if (audioPlayer.value) {
    duration.value = audioPlayer.value.duration
  }
}

function onAudioError(e) {
  console.error('Audio error:', e)
  ElMessage.error('音频文件加载失败')
}

function isActiveSegment(segment) {
  return currentTime.value >= segment.start_time && currentTime.value <= segment.end_time
}

function scrollToActiveSegment() {
  if (activeSegmentEl.value && subtitleContainer.value) {
    activeSegmentEl.value.scrollIntoView({
      behavior: 'smooth',
      block: 'center'
    })
  }
}

function formatTime(seconds) {
  if (!seconds) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

async function generateSummary() {
  summaryLoading.value = true
  summary.value = ''
  
  try {
    await llmApi.summarize(
      props.audio.id,
      '请总结以下转写内容的主要观点和要点',
      (token) => {
        summary.value += token
      },
      Object.keys(speakerNames).length > 0 ? { ...speakerNames } : null
    )
  } catch (e) {
    if (e.message && e.message.includes('运行中')) {
      ElMessage.warning(e.message)
    } else {
      ElMessage.error('生成总结失败')
    }
    console.error('Summary error:', e)
  } finally {
    summaryLoading.value = false
  }
}
</script>

<style scoped>
.playback-review {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.fixed-section {
  flex-shrink: 0;
  border-bottom: 0.5px solid rgba(0, 0, 0, 0.1);
}

.playback-header {
  padding: 16px 20px;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-top h3 {
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

.player-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.play-btn {
  width: 40px;
  height: 40px;
  background: #007AFF;
  border: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: white;
}

.play-btn:hover {
  background: #0056CC;
}

.play-btn svg {
  width: 20px;
  height: 20px;
}

.progress-container {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.time {
  font-size: 12px;
  color: #8E8E93;
  font-variant-numeric: tabular-nums;
  min-width: 40px;
}

.progress-bar {
  flex: 1;
  height: 4px;
  background: #E5E5EA;
  border-radius: 2px;
  position: relative;
  cursor: pointer;
}

.progress-fill {
  height: 100%;
  background: #007AFF;
  border-radius: 2px;
}

.progress-handle {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 12px;
  height: 12px;
  background: #007AFF;
  border-radius: 50%;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.summary-section {
  padding: 16px 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-header h4 {
  font-size: 15px;
  font-weight: 600;
  color: #1C1C1E;
  margin: 0;
}

.summarize-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(255, 149, 0, 0.1);
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #FF9500;
  cursor: pointer;
}

.summarize-btn:hover:not(:disabled) {
  background: rgba(255, 149, 0, 0.2);
}

.summarize-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.summary-content {
  padding: 12px;
  background: #F2F2F7;
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.6;
  color: #1C1C1E;
  max-height: 150px;
  overflow-y: auto;
}

.summary-empty {
  padding: 20px;
  text-align: center;
  color: #8E8E93;
}

.summary-empty p {
  margin: 0;
  font-size: 14px;
}

.scrollable-section {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.subtitle-item {
  display: flex;
  align-items: baseline;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
}

.subtitle-item:hover {
  background: rgba(0, 122, 255, 0.05);
}

.subtitle-item.active {
  background: rgba(0, 122, 255, 0.1);
}

.subtitle-time {
  font-size: 12px;
  color: #007AFF;
  font-variant-numeric: tabular-nums;
  min-width: 40px;
}

.subtitle-speaker {
  font-size: 12px;
  font-weight: 500;
  color: #fff;
  padding: 1px 8px;
  border-radius: 4px;
  min-width: 60px;
  text-align: center;
}

.subtitle-text {
  font-size: 14px;
  color: #1C1C1E;
  line-height: 1.4;
}
</style>