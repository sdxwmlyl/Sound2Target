<template>
  <div class="history-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>转写历史</span>
          <el-input
            v-model="searchKeyword"
            placeholder="搜索转写内容"
            style="width: 200px"
            @keyup.enter="searchContent"
          >
            <template #append>
              <el-button @click="searchContent">
                <el-icon><Search /></el-icon>
              </el-button>
            </template>
          </el-input>
        </div>
      </template>
      
      <el-table :data="history" v-loading="loading" stripe>
        <el-table-column prop="project_name" label="项目" width="150" />
        <el-table-column prop="session_name" label="会话" width="150" />
        <el-table-column prop="audio_filename" label="文件名" />
        <el-table-column label="时长" width="80">
          <template #default="{ row }">
            {{ formatDuration(row.duration) }}
          </template>
        </el-table-column>
        <el-table-column prop="segments_count" label="段落" width="80" />
        <el-table-column prop="speakers_count" label="发言人" width="80" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">
              {{ statusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="150" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button 
              size="small" 
              :disabled="row.status !== 'completed'"
              @click="$router.push(`/transcript/${row.audio_file_id}`)"
            >
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog v-model="showSearchResult" title="搜索结果" width="600px">
      <el-table :data="searchResults" stripe size="small">
        <el-table-column prop="project_name" label="项目" width="100" />
        <el-table-column prop="filename" label="文件" width="120" />
        <el-table-column label="时间" width="80">
          <template #default="{ row }">
            {{ formatTime(row.start_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="speaker_id" label="发言人" width="60" />
        <el-table-column prop="text" label="内容" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'

const history = ref([])
const loading = ref(false)
const searchKeyword = ref('')
const showSearchResult = ref(false)
const searchResults = ref([])

onMounted(async () => {
  await loadHistory()
})

async function loadHistory() {
  loading.value = true
  try {
    const res = await fetch('/api/history')
    history.value = await res.json()
  }
  catch (e) {
    ElMessage.error('加载历史失败')
  }
  finally {
    loading.value = false
  }
}

async function searchContent() {
  if (!searchKeyword.value.trim()) return
  
  try {
    const res = await fetch(`/api/search?keyword=${encodeURIComponent(searchKeyword.value)}`)
    searchResults.value = await res.json()
    showSearchResult.value = true
  }
  catch (e) {
    ElMessage.error('搜索失败')
  }
}

function formatDuration(seconds) {
  if (!seconds) return '-'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function formatTime(seconds) {
  return formatDuration(seconds)
}

function statusType(status) {
  const map = { pending: 'info', processing: 'warning', completed: 'success', failed: 'danger' }
  return map[status] || 'info'
}

function statusText(status) {
  const map = { pending: '待处理', processing: '处理中', completed: '完成', failed: '失败' }
  return map[status] || status
}
</script>

<style scoped>
.history-page {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>