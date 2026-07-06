<template>
  <div class="dashboard">
    <!-- Stats Cards -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon projects">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 7v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-6l-2-2H5a2 2 0 0 0-2 2z"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ stats.total_projects }}</span>
          <span class="stat-label">项目总数</span>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon files">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 18V5l12-2v13"/>
            <circle cx="6" cy="18" r="3"/>
            <circle cx="18" cy="16" r="3"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ stats.total_audio_files }}</span>
          <span class="stat-label">音频文件</span>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon completed">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ stats.completed_files }}</span>
          <span class="stat-label">已完成转写</span>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon duration">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ stats.total_duration_hours }}</span>
          <span class="stat-label">转写时长(小时)</span>
        </div>
      </div>
    </div>
    
    <!-- Status Overview -->
    <div class="section-grid">
      <div class="card">
        <div class="card-header">
          <h3>转写状态分布</h3>
        </div>
        <div class="status-bars">
          <div class="status-bar">
            <div class="status-label-row">
              <span class="status-dot success"></span>
              <span class="status-name">已完成</span>
              <span class="status-count">{{ stats.completed_files }}</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill success" :style="{ width: getProgress('completed') }"></div>
            </div>
          </div>
          
          <div class="status-bar">
            <div class="status-label-row">
              <span class="status-dot processing"></span>
              <span class="status-name">处理中</span>
              <span class="status-count">{{ getProcessingCount() }}</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill processing" :style="{ width: getProgress('processing') }"></div>
            </div>
          </div>
          
          <div class="status-bar">
            <div class="status-label-row">
              <span class="status-dot error"></span>
              <span class="status-name">失败</span>
              <span class="status-count">{{ stats.failed_files }}</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill error" :style="{ width: getProgress('failed') }"></div>
            </div>
          </div>
          
          <div class="status-bar">
            <div class="status-label-row">
              <span class="status-dot pending"></span>
              <span class="status-name">待处理</span>
              <span class="status-count">{{ stats.pending_files }}</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill pending" :style="{ width: getProgress('pending') }"></div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="card">
        <div class="card-header">
          <h3>快捷操作</h3>
        </div>
        <div class="quick-actions">
          <button class="action-btn" @click="$router.push('/projects')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 7v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-6l-2-2H5a2 2 0 0 0-2 2z"/>
              <line x1="12" y1="11" x2="12" y2="17"/>
              <line x1="9" y1="14" x2="15" y2="14"/>
            </svg>
            <span>新建项目</span>
          </button>
          
          <button class="action-btn" @click="$router.push('/history')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
            <span>转写历史</span>
          </button>
          
          <button class="action-btn" @click="$router.push('/settings')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
            <span>系统设置</span>
          </button>
        </div>
        
        <div class="info-section">
          <h4>转写段落统计</h4>
          <p class="info-value">{{ stats.total_segments }} 个段落已识别</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const stats = ref({
  total_projects: 0,
  total_sessions: 0,
  total_audio_files: 0,
  total_segments: 0,
  completed_files: 0,
  failed_files: 0,
  pending_files: 0,
  total_duration_hours: 0
})

onMounted(async () => {
  await loadStats()
})

async function loadStats() {
  try {
    const res = await fetch('/api/statistics')
    stats.value = await res.json()
  } catch (e) {
    console.error('Load stats error:', e)
  }
}

function getProcessingCount() {
  return stats.value.total_audio_files - stats.value.completed_files - stats.value.failed_files - stats.value.pending_files
}

function getProgress(type) {
  const total = stats.value.total_audio_files || 1
  const counts = {
    completed: stats.value.completed_files,
    processing: getProcessingCount(),
    failed: stats.value.failed_files,
    pending: stats.value.pending_files
  }
  return `${(counts[type] / total * 100)}%`
}
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: box-shadow 200ms ease;
}

.stat-card:hover {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon svg {
  width: 24px;
  height: 24px;
}

.stat-icon.projects {
  background: rgba(37, 99, 235, 0.1);
  color: #2563eb;
}

.stat-icon.files {
  background: rgba(99, 102, 241, 0.1);
  color: #6366f1;
}

.stat-icon.completed {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.stat-icon.duration {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
}

.stat-label {
  font-size: 14px;
  color: #64748b;
}

.section-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 24px;
}

.card-header {
  margin-bottom: 20px;
}

.card-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
}

.status-bars {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.status-bar {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-label-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.success { background: #22c55e; }
.status-dot.processing { background: #f59e0b; animation: pulse 1.5s infinite; }
.status-dot.error { background: #ef4444; }
.status-dot.pending { background: #94a3b8; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-name {
  font-size: 14px;
  color: #475569;
}

.status-count {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
  margin-left: auto;
}

.progress-bar {
  height: 8px;
  background: #f1f5f9;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 300ms ease;
}

.progress-fill.success { background: #22c55e; }
.progress-fill.processing { background: #f59e0b; }
.progress-fill.error { background: #ef4444; }
.progress-fill.pending { background: #94a3b8; }

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  color: #0f172a;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 150ms ease;
}

.action-btn:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.action-btn svg {
  width: 20px;
  height: 20px;
  color: #64748b;
}

.info-section {
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
}

.info-section h4 {
  font-size: 14px;
  font-weight: 600;
  color: #475569;
  margin: 0 0 8px 0;
}

.info-value {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .section-grid {
    grid-template-columns: 1fr;
  }
}
</style>