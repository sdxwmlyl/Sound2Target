<template>
  <div class="app">
    <nav class="nav-bar" v-if="showNav">
      <router-link to="/dashboard" class="nav-item">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="3" width="7" height="7"/>
          <rect x="14" y="3" width="7" height="7"/>
          <rect x="14" y="14" width="7" height="7"/>
          <rect x="3" y="14" width="7" height="7"/>
        </svg>
        <span>工作台</span>
      </router-link>
      <router-link to="/projects" class="nav-item">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 7v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-6l-2-2H5a2 2 0 0 0-2 2z"/>
        </svg>
        <span>项目</span>
      </router-link>
      <router-link to="/settings" class="nav-item">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="3"/>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
        </svg>
        <span>设置</span>
      </router-link>
    </nav>
    
    <router-view />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

// 在项目详情页不显示底部导航
const showNav = computed(() => {
  return !route.path.startsWith('/project/')
})
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body {
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: #F2F2F7;
  color: #1C1C1E;
}

.app {
  min-height: 100vh;
  padding-bottom: 60px;
}

.nav-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-around;
  padding: 8px 0;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 0.5px solid rgba(0, 0, 0, 0.1);
  z-index: 100;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 4px 16px;
  text-decoration: none;
  color: #8E8E93;
  font-size: 10px;
  transition: color 150ms ease;
}

.nav-item:hover,
.nav-item.router-link-active {
  color: #007AFF;
}

.nav-item svg {
  width: 24px;
  height: 24px;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(142, 142, 147, 0.3);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(142, 142, 147, 0.5);
}

/* 全局动画 */
button {
  cursor: pointer;
  transition: all 150ms ease;
}

button:active {
  transform: scale(0.98);
}

input, textarea {
  font-family: inherit;
}

/* Markdown样式 */
.markdown-body {
  font-size: 14px;
  line-height: 1.6;
  color: #1C1C1E;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4,
.markdown-body h5,
.markdown-body h6 {
  margin-top: 16px;
  margin-bottom: 8px;
  font-weight: 600;
}

.markdown-body h1 { font-size: 20px; }
.markdown-body h2 { font-size: 18px; }
.markdown-body h3 { font-size: 16px; }

.markdown-body p {
  margin-bottom: 8px;
}

.markdown-body ul,
.markdown-body ol {
  margin-bottom: 8px;
  padding-left: 20px;
}

.markdown-body li {
  margin-bottom: 4px;
}

.markdown-body code {
  background: rgba(142, 142, 147, 0.12);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  font-family: 'SF Mono', Monaco, Menlo, Consolas, monospace;
}

.markdown-body pre {
  background: rgba(142, 142, 147, 0.12);
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin-bottom: 12px;
}

.markdown-body pre code {
  background: none;
  padding: 0;
}

.markdown-body blockquote {
  border-left: 3px solid #007AFF;
  padding-left: 12px;
  margin-left: 0;
  margin-bottom: 12px;
  color: #8E8E93;
}

.markdown-body table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 12px;
}

.markdown-body th,
.markdown-body td {
  border: 1px solid rgba(0, 0, 0, 0.1);
  padding: 8px 12px;
  text-align: left;
}

.markdown-body th {
  background: rgba(142, 142, 147, 0.08);
  font-weight: 600;
}

.markdown-body strong {
  font-weight: 600;
}

.markdown-body em {
  font-style: italic;
}

.markdown-body a {
  color: #007AFF;
  text-decoration: none;
}

.markdown-body a:hover {
  text-decoration: underline;
}
</style>