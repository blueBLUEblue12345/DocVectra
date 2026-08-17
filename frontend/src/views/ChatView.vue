<template>
  <div class="chat-view">
    <div class="chat-header">
      <h1>智能问答</h1>
      <p class="subtitle">基于知识库的智能对话助手</p>
    </div>

    <div class="messages-container" ref="messagesContainer">
      <div v-if="messages.length === 0" class="empty-state">
        <div class="empty-icon">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
        </div>
        <h2>开始对话</h2>
        <p>输入您的问题，我将基于知识库为您提供答案</p>
      </div>

      <div
        v-for="message in messages"
        :key="message.id"
        class="message"
        :class="message.role"
      >
        <div class="message-avatar">
          <div v-if="message.role === 'user'" class="user-avatar">U</div>
          <div v-else class="assistant-avatar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2L2 7L12 12L22 7L12 2Z"></path>
              <path d="M2 17L12 22L22 17"></path>
              <path d="M2 12L12 17L22 12"></path>
            </svg>
          </div>
        </div>
        <div class="message-content">
          <div class="message-text" v-html="renderMarkdown(message.content)"></div>
          <div v-if="message.isStreaming" class="streaming-indicator">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
        </div>
      </div>

      <div v-if="isLoading && messages.length > 0 && messages[messages.length - 1].content === ''" class="thinking">
        <div class="thinking-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>

    <div class="input-area">
      <div class="input-wrapper">
        <textarea
          v-model="inputMessage"
          @keydown.enter.exact.prevent="sendMessage"
          @input="autoResize"
          ref="textareaRef"
          placeholder="输入您的问题..."
          rows="1"
          :disabled="isLoading"
        ></textarea>
        <button
          class="send-btn"
          @click="sendMessage"
          :disabled="!inputMessage.trim() || isLoading"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </div>
      <p class="input-hint">按 Enter 发送，Shift + Enter 换行</p>
    </div>

    <PixelNailong />
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useChatStore } from '../stores/chatStore'
import { marked } from 'marked'
import PixelNailong from '../components/PixelNailong.vue'

const chatStore = useChatStore()
const messagesContainer = ref(null)
const textareaRef = ref(null)
const inputMessage = ref('')

const messages = computed(() => chatStore.messages)
const isLoading = computed(() => chatStore.isLoading)

const renderMarkdown = (content) => {
  if (!content) return ''
  return marked(content, { breaks: true, gfm: true })
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const autoResize = () => {
  const textarea = textareaRef.value
  if (textarea) {
    textarea.style.height = 'auto'
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px'
  }
}

const sendMessage = () => {
  const content = inputMessage.value.trim()
  if (!content || isLoading.value) return

  inputMessage.value = ''
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
  }

  chatStore.sendMessage(content)
}

watch(messages, () => {
  scrollToBottom()
}, { deep: true })

onMounted(() => {
  if (!chatStore.currentSessionId) {
    chatStore.createNewSession()
  }
})
</script>

<style scoped>
.chat-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-primary);
}

.chat-header {
  padding: 20px 32px;
  border-bottom: 1px solid var(--border-color);
}

.chat-header h1 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.subtitle {
  font-size: 13px;
  color: var(--text-tertiary);
  margin-top: 4px;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
}

.empty-icon {
  width: 80px;
  height: 80px;
  background: var(--bg-secondary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  margin-bottom: 16px;
}

.empty-state h2 {
  font-size: 18px;
  font-weight: 500;
  color: var(--text-primary);
  margin: 0 0 8px;
}

.empty-state p {
  font-size: 14px;
  color: var(--text-tertiary);
  margin: 0;
}

.message {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-avatar {
  flex-shrink: 0;
}

.user-avatar, .assistant-avatar {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.user-avatar {
  background: var(--primary-color);
  color: white;
}

.assistant-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-text {
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-primary);
  word-wrap: break-word;
}

.message-text :deep(p) {
  margin: 0 0 12px;
}

.message-text :deep(p:last-child) {
  margin-bottom: 0;
}

.message-text :deep(code) {
  background: var(--bg-secondary);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}

.message-text :deep(pre) {
  background: #1e1e1e;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
}

.message-text :deep(pre code) {
  background: none;
  padding: 0;
  color: #d4d4d4;
}

.streaming-indicator {
  display: inline-flex;
  gap: 4px;
  margin-left: 4px;
}

.streaming-indicator .dot {
  width: 6px;
  height: 6px;
  background: var(--primary-color);
  border-radius: 50%;
  animation: pulse 1.4s infinite;
}

.streaming-indicator .dot:nth-child(2) {
  animation-delay: 0.2s;
}

.streaming-indicator .dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes pulse {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1); }
}

.thinking {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.thinking-dots {
  display: flex;
  gap: 6px;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-radius: 12px;
}

.thinking-dots span {
  width: 8px;
  height: 8px;
  background: var(--text-tertiary);
  border-radius: 50%;
  animation: bounce 1.4s infinite;
}

.thinking-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.thinking-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-8px); }
}

.input-area {
  padding: 16px 32px 24px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-primary);
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 12px 16px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input-wrapper:focus-within {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.input-wrapper textarea {
  flex: 1;
  background: none;
  resize: none;
  color: var(--text-primary);
  min-height: 24px;
  max-height: 200px;
}

.input-wrapper textarea::placeholder {
  color: var(--text-tertiary);
}

.input-wrapper textarea:disabled {
  opacity: 0.6;
}

.send-btn {
  width: 36px;
  height: 36px;
  background: var(--primary-color);
  color: white;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s, opacity 0.2s;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  background: var(--primary-hover);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-hint {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 8px;
  text-align: center;
}
</style>
