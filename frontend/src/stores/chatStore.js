import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { v4 as uuidv4 } from 'uuid'
import api from '../services/api'

export const useChatStore = defineStore('chat', () => {
  const sessions = ref([])
  const currentSessionId = ref(null)
  const messages = ref([])
  const isLoading = ref(false)
  const isStreaming = ref(false)

  const currentSession = computed(() =>
    sessions.value.find(s => s.id === currentSessionId.value)
  )

  const createNewSession = () => {
    const newSession = {
      id: uuidv4(),
      title: '新对话',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
    sessions.value.unshift(newSession)
    currentSessionId.value = newSession.id
    messages.value = []
    return newSession
  }

  const switchSession = (sessionId) => {
    currentSessionId.value = sessionId
    loadSessionMessages(sessionId)
  }

  const deleteSession = (sessionId) => {
    const index = sessions.value.findIndex(s => s.id === sessionId)
    if (index !== -1) {
      sessions.value.splice(index, 1)
      if (currentSessionId.value === sessionId) {
        if (sessions.value.length > 0) {
          currentSessionId.value = sessions.value[0].id
          loadSessionMessages(sessions.value[0].id)
        } else {
          createNewSession()
        }
      }
    }
  }

  const loadSessionMessages = async (sessionId) => {
    try {
      const response = await api.getHistory(sessionId)
      messages.value = (response.items || []).map(item => ({
        id: item._id || item.id,
        role: item.role,
        content: item.text,
        timestamp: item.ts
      }))
    } catch (error) {
      console.error('Failed to load messages:', error)
      messages.value = []
    }
  }

  const addMessage = (message) => {
    messages.value.push(message)
    if (currentSession.value) {
      currentSession.value.updatedAt = new Date().toISOString()
      if (messages.value.length === 1 && message.role === 'user') {
        currentSession.value.title = message.content.slice(0, 30) + (message.content.length > 30 ? '...' : '')
      }
    }
  }

  const updateLastAssistantMessage = (content) => {
    const lastMessage = messages.value[messages.value.length - 1]
    if (lastMessage && lastMessage.role === 'assistant') {
      lastMessage.content = content
    }
  }

  const sendMessage = async (content) => {
    if (!currentSessionId.value) {
      createNewSession()
    }

    addMessage({
      id: uuidv4(),
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    })

    addMessage({
      id: uuidv4(),
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      isStreaming: true
    })

    isLoading.value = true
    isStreaming.value = true

    try {
      const response = await api.sendQuery(content, currentSessionId.value, true)

      if (response.eventSource) {
        let fullContent = ''

        response.eventSource.addEventListener('delta', (event) => {
          try {
            const data = JSON.parse(event.data)
            fullContent += data.content || ''
            updateLastAssistantMessage(fullContent)
          } catch (e) {
            console.error('Parse delta error:', e)
          }
        })

        response.eventSource.addEventListener('final', (event) => {
          try {
            const data = JSON.parse(event.data)
            if (data.answer) {
              updateLastAssistantMessage(data.answer)
            }
          } catch (e) {
            console.error('Parse final error:', e)
          }
          isStreaming.value = false
          const lastMsg = messages.value[messages.value.length - 1]
          if (lastMsg) lastMsg.isStreaming = false
          response.eventSource.close()
        })

        response.eventSource.addEventListener('error', (event) => {
          try {
            const data = JSON.parse(event.data)
            updateLastAssistantMessage(data.error || '发生错误')
          } catch (e) {
            updateLastAssistantMessage('发生错误')
          }
          isStreaming.value = false
          const lastMsg = messages.value[messages.value.length - 1]
          if (lastMsg) lastMsg.isStreaming = false
          response.eventSource.close()
        })

        response.eventSource.onerror = () => {
          isStreaming.value = false
          isLoading.value = false
          const lastMsg = messages.value[messages.value.length - 1]
          if (lastMsg) lastMsg.isStreaming = false
          response.eventSource.close()
        }
      } else if (response.answer) {
        updateLastAssistantMessage(response.answer)
        isStreaming.value = false
        const lastMsg = messages.value[messages.value.length - 1]
        if (lastMsg) lastMsg.isStreaming = false
      }
    } catch (error) {
      console.error('Send message error:', error)
      updateLastAssistantMessage('抱歉，发生了错误，请重试。')
      isStreaming.value = false
      const lastMsg = messages.value[messages.value.length - 1]
      if (lastMsg) lastMsg.isStreaming = false
    } finally {
      isLoading.value = false
    }
  }

  return {
    sessions,
    currentSessionId,
    messages,
    isLoading,
    isStreaming,
    currentSession,
    createNewSession,
    switchSession,
    deleteSession,
    loadSessionMessages,
    addMessage,
    sendMessage
  }
})
