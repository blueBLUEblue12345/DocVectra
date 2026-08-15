<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <div class="logo">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>DocVectra</span>
      </div>
    </div>

    <div class="sidebar-actions">
      <button class="new-chat-btn" @click="newChat">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"></line>
          <line x1="5" y1="12" x2="19" y2="12"></line>
        </svg>
        <span>新对话</span>
      </button>
    </div>

    <div class="nav-section">
      <router-link to="/chat" class="nav-item" :class="{ active: $route.path === '/chat' }">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
        <span>智能问答</span>
      </router-link>
      <router-link to="/import" class="nav-item" :class="{ active: $route.path === '/import' }">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="17 8 12 3 7 8"></polyline>
          <line x1="12" y1="3" x2="12" y2="15"></line>
        </svg>
        <span>文档导入</span>
      </router-link>
    </div>

    <div class="history-section">
      <div class="section-title">历史对话</div>
      <div class="history-list">
        <div
          v-for="session in sessions"
          :key="session.id"
          class="history-item"
          :class="{ active: currentSessionId === session.id }"
          @click="switchSession(session.id)"
        >
          <span class="history-title">{{ session.title }}</span>
          <button class="delete-btn" @click.stop="deleteSession(session.id)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
          </button>
        </div>
        <div v-if="sessions.length === 0" class="empty-history">
          暂无历史对话
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '../stores/chatStore'

const router = useRouter()
const chatStore = useChatStore()

const sessions = computed(() => chatStore.sessions)
const currentSessionId = computed(() => chatStore.currentSessionId)

const newChat = () => {
  chatStore.createNewSession()
  router.push('/chat')
}

const switchSession = (sessionId) => {
  chatStore.switchSession(sessionId)
  router.push('/chat')
}

const deleteSession = (sessionId) => {
  chatStore.deleteSession(sessionId)
}
</script>

<style scoped>
.sidebar {
  width: 260px;
  background: var(--bg-primary);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.sidebar-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.logo svg {
  color: var(--primary-color);
}

.sidebar-actions {
  padding: 16px;
}

.new-chat-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--primary-color);
  color: white;
  border-radius: var(--radius-md);
  font-weight: 500;
  transition: background 0.2s;
}

.new-chat-btn:hover {
  background: var(--primary-hover);
}

.nav-section {
  padding: 8px 12px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  transition: all 0.2s;
  margin-bottom: 4px;
}

.nav-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.nav-item.active {
  background: var(--bg-hover);
  color: var(--primary-color);
}

.history-section {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 0 12px 12px;
}

.section-title {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 12px 12px 8px;
}

.history-list {
  flex: 1;
  overflow-y: auto;
}

.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 2px;
}

.history-item:hover {
  background: var(--bg-hover);
}

.history-item.active {
  background: var(--bg-hover);
}

.history-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  color: var(--text-secondary);
}

.delete-btn {
  opacity: 0;
  padding: 4px;
  color: var(--text-tertiary);
  border-radius: 4px;
  transition: all 0.2s;
}

.history-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background: #fee2e2;
  color: #dc2626;
}

.empty-history {
  padding: 20px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 13px;
}
</style>
