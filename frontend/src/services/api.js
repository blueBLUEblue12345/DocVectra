import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api/query',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

const importClient = axios.create({
  baseURL: '/api/import',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
})

export default {
  async sendQuery(query, sessionId, isStream = false) {
    const response = await apiClient.post('/query', {
      query,
      session_id: sessionId,
      is_stream: isStream
    })

    if (isStream) {
      const eventSource = new EventSource(
        `/api/query/stream/${sessionId}`
      )
      return { eventSource, postResult: response.data }
    }

    return response.data
  },

  async getHistory(sessionId) {
    const response = await apiClient.get(`/history/${sessionId}`)
    return response.data
  },

  async clearHistory(sessionId) {
    const response = await apiClient.delete(`/history/${sessionId}`)
    return response.data
  },

  async uploadFile(files) {
    const formData = new FormData()
    const fileArray = Array.isArray(files) ? files : [files]
    for (const file of fileArray) {
      formData.append('files', file)
    }

    const response = await importClient.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  async getTaskStatus(taskId) {
    const response = await importClient.get(`/status/${taskId}`)
    return response.data
  }
}
