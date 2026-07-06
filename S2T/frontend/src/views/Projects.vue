<template>
  <div class="projects-page">
    <header class="page-header">
      <h1 class="page-title">S2T 语音转写</h1>
      <button class="create-btn" @click="showCreateDialog = true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        <span>新建项目</span>
      </button>
    </header>
    
    <div class="projects-grid">
      <div 
        v-for="project in projects" 
        :key="project.id"
        class="project-card"
        @click="$router.push(`/project/${project.id}`)"
      >
        <div class="card-header">
          <div class="card-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 7v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-6l-2-2H5a2 2 0 0 0-2 2z"/>
            </svg>
          </div>
          <div class="card-actions">
            <button class="action-btn" @click.stop="handleDelete(project.id)" title="删除">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              </svg>
            </button>
          </div>
        </div>
        <div class="card-body">
          <h3 class="card-title">{{ project.name }}</h3>
          <p class="card-desc">{{ project.description || '暂无描述' }}</p>
          <div class="card-stats">
            <span class="stat">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                <path d="M9 18V5l12-2v13"/>
                <circle cx="6" cy="18" r="3"/>
                <circle cx="18" cy="16" r="3"/>
              </svg>
              {{ project.audio_count || 0 }} 个音频
            </span>
            <span class="stat">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              {{ project.completed_count || 0 }} 已完成
            </span>
          </div>
        </div>
        <div class="card-footer">
          <span class="card-time">{{ formatDate(project.updated_at) }}</span>
        </div>
      </div>
      
      <div v-if="projects.length === 0" class="empty-card" @click="showCreateDialog = true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        <span>创建第一个项目</span>
      </div>
    </div>
    
    <!-- 创建项目弹窗 -->
    <div class="dialog-overlay" v-if="showCreateDialog" @click="showCreateDialog = false">
      <div class="dialog" @click.stop>
        <div class="dialog-header">
          <h3>新建项目</h3>
          <button class="close-btn" @click="showCreateDialog = false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="dialog-body">
          <div class="form-group">
            <label>项目名称</label>
            <input v-model="newProject.name" placeholder="输入项目名称" @keyup.enter="handleCreate" />
          </div>
          <div class="form-group">
            <label>项目描述</label>
            <textarea v-model="newProject.description" placeholder="输入项目描述（可选）" rows="3"></textarea>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn-cancel" @click="showCreateDialog = false">取消</button>
          <button class="btn-create" @click="handleCreate" :disabled="!newProject.name">创建</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { projectApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const projects = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const newProject = ref({ name: '', description: '' })

onMounted(async () => {
  await loadProjects()
})

async function loadProjects() {
  loading.value = true
  try {
    const res = await projectApi.list()
    projects.value = res.data
  } catch (e) {
    console.error('Load projects error:', e)
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!newProject.value.name) {
    ElMessage.warning('请输入项目名称')
    return
  }
  
  try {
    await projectApi.create(newProject.value)
    ElMessage.success('项目创建成功')
    showCreateDialog.value = false
    newProject.value = { name: '', description: '' }
    await loadProjects()
  } catch (e) {
    ElMessage.error('创建失败')
  }
}

async function handleDelete(id) {
  try {
    await ElMessageBox.confirm('确定删除该项目？此操作不可恢复。', '删除确认', { type: 'warning' })
    await projectApi.delete(id)
    ElMessage.success('项目已删除')
    await loadProjects()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit' 
  })
}
</script>

<style scoped>
.projects-page {
  min-height: 100vh;
  background: #F2F2F7;
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto 24px;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: #1C1C1E;
  margin: 0;
}

.create-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: #007AFF;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 500;
  color: white;
  cursor: pointer;
  transition: background 150ms ease;
}

.create-btn:hover {
  background: #0056CC;
}

.create-btn svg {
  width: 18px;
  height: 18px;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.project-card {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 16px;
  border: 0.5px solid rgba(0, 0, 0, 0.1);
  padding: 20px;
  cursor: pointer;
  transition: all 200ms ease;
}

.project-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.card-icon {
  width: 44px;
  height: 44px;
  background: rgba(0, 122, 255, 0.1);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #007AFF;
}

.card-icon svg {
  width: 22px;
  height: 22px;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  width: 32px;
  height: 32px;
  background: rgba(142, 142, 147, 0.12);
  border: none;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8E8E93;
  cursor: pointer;
  opacity: 0;
  transition: all 150ms ease;
}

.project-card:hover .action-btn {
  opacity: 1;
}

.action-btn:hover {
  background: rgba(255, 59, 48, 0.12);
  color: #FF3B30;
}

.action-btn svg {
  width: 16px;
  height: 16px;
}

.card-body {
  margin-bottom: 16px;
}

.card-title {
  font-size: 17px;
  font-weight: 600;
  color: #1C1C1E;
  margin: 0 0 8px 0;
}

.card-desc {
  font-size: 14px;
  color: #8E8E93;
  margin: 0 0 12px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-stats {
  display: flex;
  gap: 16px;
}

.stat {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #8E8E93;
}

.card-footer {
  padding-top: 12px;
  border-top: 0.5px solid rgba(0, 0, 0, 0.06);
}

.card-time {
  font-size: 12px;
  color: #AEAEB2;
}

.empty-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  background: rgba(255, 255, 255, 0.5);
  border: 2px dashed rgba(0, 0, 0, 0.1);
  border-radius: 16px;
  cursor: pointer;
  color: #8E8E93;
  transition: all 200ms ease;
}

.empty-card:hover {
  background: rgba(255, 255, 255, 0.8);
  border-color: #007AFF;
  color: #007AFF;
}

.empty-card svg {
  margin-bottom: 12px;
}

.empty-card span {
  font-size: 15px;
  font-weight: 500;
}

/* Dialog styles */
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.dialog {
  width: 420px;
  background: white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
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

.dialog-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #8E8E93;
  margin-bottom: 8px;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 12px;
  font-size: 15px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 10px;
  background: #F2F2F7;
  font-family: inherit;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #007AFF;
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.15);
}

.form-group textarea {
  resize: vertical;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 0.5px solid rgba(0, 0, 0, 0.1);
}

.btn-cancel {
  padding: 10px 20px;
  background: rgba(142, 142, 147, 0.12);
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 500;
  color: #1C1C1E;
  cursor: pointer;
}

.btn-create {
  padding: 10px 20px;
  background: #007AFF;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 500;
  color: white;
  cursor: pointer;
}

.btn-create:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>