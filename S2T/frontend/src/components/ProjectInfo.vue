<template>
  <div class="project-info">
    <div class="info-grid">
      <!-- 左侧：基本信息 -->
      <div class="info-section">
        <div class="info-row">
          <span class="info-label">创建时间</span>
          <span class="info-value">{{ formatDate(project?.created_at) }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">描述</span>
          <span class="info-value description">{{ project?.description || '暂无描述' }}</span>
        </div>
      </div>
      
      <!-- 右侧：热词 -->
      <div class="info-section">
        <div class="hotwords-header">
          <span class="info-label">热词配置</span>
          <button class="edit-btn" @click="showHotwordsDialog = true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
            <span>编辑</span>
          </button>
        </div>
        <div class="hotwords-content">
          <span v-if="project?.hotwords" class="hotwords-text">{{ project.hotwords }}</span>
          <span v-else class="hotwords-empty">未配置热词</span>
        </div>
      </div>
    </div>
    
    <!-- 热词编辑弹窗 -->
    <Teleport to="body">
      <div class="dialog-overlay" v-if="showHotwordsDialog" @click="showHotwordsDialog = false">
        <div class="dialog" @click.stop>
          <div class="dialog-header">
            <h3>编辑热词</h3>
            <button class="close-btn" @click="showHotwordsDialog = false">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
          <div class="dialog-body">
            <p class="dialog-hint">多个热词用空格分隔，例如：人工智能 机器学习 深度学习</p>
            <textarea 
              v-model="editingHotwords" 
              class="hotwords-input"
              rows="4"
              placeholder="输入热词，用空格分隔"
            ></textarea>
          </div>
          <div class="dialog-footer">
            <button class="btn-cancel" @click="showHotwordsDialog = false">取消</button>
            <button class="btn-save" @click="saveHotwords">保存</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  project: Object
})

const emit = defineEmits(['update-hotwords'])

const showHotwordsDialog = ref(false)
const editingHotwords = ref('')

watch(() => props.project?.hotwords, (val) => {
  editingHotwords.value = val || ''
}, { immediate: true })

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function saveHotwords() {
  emit('update-hotwords', editingHotwords.value)
  showHotwordsDialog.value = false
}
</script>

<style scoped>
.project-info {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 20px;
  border: 0.5px solid rgba(0, 0, 0, 0.1);
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.info-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 13px;
  color: #8E8E93;
  font-weight: 500;
}

.info-value {
  font-size: 15px;
  color: #1C1C1E;
}

.info-value.description {
  color: #3C3C43;
}

.hotwords-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.edit-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: rgba(0, 122, 255, 0.1);
  border: none;
  border-radius: 8px;
  color: #007AFF;
  font-size: 13px;
  cursor: pointer;
  transition: background 150ms ease;
}

.edit-btn:hover {
  background: rgba(0, 122, 255, 0.2);
}

.hotwords-content {
  padding: 12px;
  background: rgba(142, 142, 147, 0.08);
  border-radius: 10px;
  min-height: 40px;
}

.hotwords-text {
  font-size: 14px;
  color: #1C1C1E;
  word-break: break-all;
}

.hotwords-empty {
  font-size: 14px;
  color: #AEAEB2;
}

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
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: rgba(142, 142, 147, 0.12);
  border: none;
  border-radius: 50%;
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

.dialog-hint {
  font-size: 13px;
  color: #8E8E93;
  margin: 0 0 12px 0;
}

.hotwords-input {
  width: 100%;
  padding: 12px;
  font-size: 15px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 10px;
  resize: vertical;
  font-family: inherit;
}

.hotwords-input:focus {
  outline: none;
  border-color: #007AFF;
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.15);
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
  transition: background 150ms ease;
}

.btn-cancel:hover {
  background: rgba(142, 142, 147, 0.2);
}

.btn-save {
  padding: 10px 20px;
  background: #007AFF;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 500;
  color: white;
  cursor: pointer;
  transition: background 150ms ease;
}

.btn-save:hover {
  background: #0056CC;
}
</style>