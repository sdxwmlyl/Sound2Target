<template>
  <div class="ai-chat">
    <!-- 顶部 -->
    <div class="chat-header">
      <h3>AI问答</h3>
      <button class="close-btn" @click="$emit('close')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>
    
    <!-- 输入区 -->
    <div class="input-section">
      <label>输入问题</label>
      <textarea 
        v-model="question" 
        placeholder="输入您的问题，AI将基于项目所有转写内容进行回答..."
        rows="3"
        @keyup.ctrl.enter="sendQuestion"
      ></textarea>
    </div>
    
    <!-- 参数设置 + 提交按钮 -->
    <div class="params-section">
      <div class="param-item">
        <label>上下文轮次</label>
        <input type="number" v-model.number="maxContext" min="1" max="10" />
      </div>
      <div class="param-item">
        <label>温度</label>
        <input type="number" v-model.number="temperature" min="0" max="1" step="0.1" />
      </div>
      <button class="send-btn" @click="sendQuestion" :disabled="!question.trim() || loading">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
          <line x1="22" y1="2" x2="11" y2="13"/>
          <polygon points="22 2 15 22 11 13 2 9 22 2"/>
        </svg>
        <span>{{ loading ? '生成中...' : '提交' }}</span>
      </button>
    </div>
    
    <!-- 回答区 -->
    <div class="answer-section">
      <div v-if="messages.length === 0" class="empty-answer">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="40" height="40">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <p>输入问题开始对话</p>
      </div>
      
      <div v-else class="messages-list">
        <div 
          v-for="(msg, i) in messages" 
          :key="i"
          class="message"
          :class="msg.role"
        >
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
          <div class="message-content">
            <div v-if="msg.loading" class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <div v-else class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { llmApi } from '@/api'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'

const props = defineProps({
  projectId: String
})

const emit = defineEmits(['close'])

const question = ref('')
const messages = ref([])
const loading = ref(false)
const maxContext = ref(3)
const temperature = ref(0.4)

onMounted(async () => {
  await loadChatHistory()
})

async function loadChatHistory() {
  try {
    const res = await llmApi.getChatHistory(props.projectId)
    messages.value = res.data.map(chat => ({
      role: chat.role,
      content: chat.content,
      loading: false
    }))
  } catch (e) {
    console.error('Load chat history error:', e)
  }
}

function renderMarkdown(content) {
  return content ? marked(content) : ''
}

async function sendQuestion() {
  if (!question.value.trim() || loading.value) return
  
  const userQuestion = question.value.trim()
  question.value = ''
  
  messages.value.push({
    role: 'user',
    content: userQuestion
  })
  
  messages.value.push({
    role: 'assistant',
    content: '',
    loading: true
  })
  
  loading.value = true
  
  try {
    const history = messages.value
      .filter(m => !m.loading)
      .slice(0, -1)
      .map(m => ({ role: m.role, content: m.content }))
    
    const lastMsg = messages.value[messages.value.length - 1]
    
    await llmApi.chat(
      props.projectId,
      userQuestion,
      history.length > 0 ? history : null,
      (token) => {
        lastMsg.content += token
      }
    )
    
    lastMsg.loading = false
  } catch (e) {
    if (e.message && e.message.includes('运行中')) {
      ElMessage.warning(e.message)
    } else {
      ElMessage.error('问答失败: ' + (e.message || '未知错误'))
    }
    messages.value.pop()
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.ai-chat {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 0.5px solid rgba(0, 0, 0, 0.1);
}

.chat-header h3 {
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

.input-section {
  padding: 16px 20px;
  border-bottom: 0.5px solid rgba(0, 0, 0, 0.1);
}

.input-section label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #8E8E93;
  margin-bottom: 8px;
}

.input-section textarea {
  width: 100%;
  padding: 12px;
  font-size: 15px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 10px;
  resize: vertical;
  font-family: inherit;
  background: #F2F2F7;
}

.input-section textarea:focus {
  outline: none;
  border-color: #007AFF;
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.15);
}

.send-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
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

.send-btn:hover:not(:disabled) {
  background: #0056CC;
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.params-section {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 12px 20px;
  border-bottom: 0.5px solid rgba(0, 0, 0, 0.1);
}

.params-section .send-btn {
  margin-left: auto;
}

.param-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.param-item label {
  font-size: 13px;
  color: #8E8E93;
}

.param-item input {
  width: 60px;
  padding: 6px 10px;
  font-size: 14px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  text-align: center;
  background: #F2F2F7;
}

.param-item input:focus {
  outline: none;
  border-color: #007AFF;
}

.answer-section {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.empty-answer {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #8E8E93;
}

.empty-answer svg {
  color: #AEAEB2;
  margin-bottom: 12px;
}

.empty-answer p {
  font-size: 15px;
  margin: 0;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  gap: 12px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 32px;
  height: 32px;
  background: #F2F2F7;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message-avatar svg {
  width: 18px;
  height: 18px;
  color: #8E8E93;
}

.message.assistant .message-avatar {
  background: rgba(0, 122, 255, 0.1);
}

.message.assistant .message-avatar svg {
  color: #007AFF;
}

.message-content {
  max-width: 80%;
  padding: 10px 14px;
  background: #F2F2F7;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  color: #1C1C1E;
  white-space: pre-wrap;
}

.message.user .message-content {
  background: #007AFF;
  color: white;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  background: #8E8E93;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 100% { opacity: 0.3; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.2); }
}
</style>