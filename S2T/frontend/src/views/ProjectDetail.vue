<template>
  <div class="project-detail">
    <!-- 顶部导航 -->
    <header class="top-bar">
      <button class="back-btn" @click="$router.push('/projects')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
        <span>返回</span>
      </button>
      <h1 class="page-title">{{ project?.name || '加载中...' }}</h1>
      <div class="spacer"></div>
    </header>
    
    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 项目信息卡 -->
      <ProjectInfo 
        :project="project" 
        @update-hotwords="handleUpdateHotwords"
      />
      
      <!-- 下方分栏 -->
      <div class="content-grid">
        <!-- 左侧：音频列表 -->
        <AudioList 
          :audio-files="audioFiles"
          :project-id="projectId"
          :has-active-recording="hasActiveProcessing"
          @refresh="loadData"
          @play="handlePlay"
          @delete="handleDeleteAudio"
          @show-ai-chat="handleShowAIChat"
        />
        
        <!-- 右侧：多功能面板 -->
        <div class="panel-wrapper">
          <MultiPanel 
            :mode="panelMode"
            :audio-files="audioFiles"
            :selected-audio="selectedAudio"
            :project-id="projectId"
            @close="handleClosePanel"
            @play="handlePlay"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { projectApi, audioApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import ProjectInfo from '@/components/ProjectInfo.vue'
import AudioList from '@/components/AudioList.vue'
import MultiPanel from '@/components/MultiPanel.vue'

const route = useRoute()
const projectId = route.params.id

const project = ref(null)
const audioFiles = ref([])
const loading = ref(false)
const panelMode = ref('default')  // default | playback | ai-chat
const selectedAudio = ref(null)

let refreshTimer = null

const hasActiveProcessing = computed(() => {
  return audioFiles.value.some(a => a.status === 'processing')
})

onMounted(async () => {
  await loadData()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})

function startAutoRefresh() {
  refreshTimer = setInterval(async () => {
    if (hasActiveProcessing.value) {
      await loadData()
    }
  }, 3000)
}

function stopAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

async function loadData() {
  try {
    const [projectRes, audioRes] = await Promise.all([
      projectApi.get(projectId),
      projectApi.getAudioFiles(projectId)
    ])
    project.value = projectRes.data
    audioFiles.value = audioRes.data
    
    // 如果之前选中的音频状态变了，更新它
    if (selectedAudio.value) {
      const updated = audioRes.data.find(a => a.id === selectedAudio.value.id)
      if (updated) selectedAudio.value = updated
    }
  } catch (e) {
    console.error('Load error:', e)
  }
}

async function handleUpdateHotwords(hotwords) {
  try {
    await projectApi.updateHotwords(projectId, hotwords)
    project.value.hotwords = hotwords
  } catch (e) {
    console.error('Update hotwords error:', e)
  }
}

function handlePlay(audio) {
  selectedAudio.value = audio
  panelMode.value = 'playback'
}

function handleShowAIChat() {
  panelMode.value = 'ai-chat'
}

function handleClosePanel() {
  panelMode.value = 'default'
  selectedAudio.value = null
}

async function handleDeleteAudio(audioId) {
  try {
    await ElMessageBox.confirm('确定删除该音频文件？', '删除确认', { type: 'warning' })
    await audioApi.delete(audioId)
    ElMessage.success('已删除')
    await loadData()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}
</script>

<style scoped>
.project-detail {
  min-height: 100vh;
  background: #F2F2F7;
}

.top-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 24px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 0.5px solid rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  background: transparent;
  border: none;
  color: #007AFF;
  font-size: 15px;
  cursor: pointer;
  border-radius: 8px;
  transition: background 150ms ease;
}

.back-btn:hover {
  background: rgba(0, 122, 255, 0.1);
}

.back-btn svg {
  width: 20px;
  height: 20px;
}

.page-title {
  font-size: 17px;
  font-weight: 600;
  color: #1C1C1E;
  margin: 0;
}

.spacer {
  flex: 1;
}

.main-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px 24px;
}

.content-grid {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: 20px;
  margin-top: 20px;
}

.panel-wrapper {
  height: calc(100vh - 280px);
  min-height: 400px;
  position: sticky;
  top: 80px;
}

@media (max-width: 1024px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
  
  .panel-wrapper {
    height: auto;
    position: static;
  }
}
</style>