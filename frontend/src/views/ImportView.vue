<template>
  <div class="import-view">
    <div class="import-header">
      <h1>文档导入</h1>
      <p class="subtitle">上传文档到知识库，支持 PDF、Markdown 格式</p>
    </div>

    <div class="import-content">
      <div
        class="upload-area"
        :class="{ dragging: isDragging, 'has-file': selectedFile }"
        @dragover.prevent="isDragging = true"
        @dragleave="isDragging = false"
        @drop.prevent="handleDrop"
        @click="triggerFileInput"
      >
        <input
          type="file"
          ref="fileInput"
          @change="handleFileSelect"
          accept=".pdf,.md,.markdown"
          style="display: none"
        />

        <div v-if="!selectedFile" class="upload-placeholder">
          <div class="upload-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
          </div>
          <h3>点击或拖拽文件到此处</h3>
          <p>支持 PDF、Markdown 格式</p>
        </div>

        <div v-else class="file-preview">
          <div class="file-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
            </svg>
          </div>
          <div class="file-info">
            <span class="file-name">{{ selectedFile.name }}</span>
            <span class="file-size">{{ formatFileSize(selectedFile.size) }}</span>
          </div>
          <button class="remove-btn" @click.stop="removeFile">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </div>

      <button
        class="upload-btn"
        @click="startUpload"
        :disabled="!selectedFile || isUploading"
      >
        <span v-if="isUploading" class="spinner"></span>
        <span>{{ isUploading ? '上传中...' : '开始上传' }}</span>
      </button>

      <div v-if="uploadTask" class="task-status">
        <div class="status-header">
          <span class="status-label">任务状态</span>
          <span class="status-badge" :class="uploadTask.status">
            {{ statusText }}
          </span>
        </div>

        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progress + '%' }"></div>
        </div>

        <div class="status-details">
          <span>{{ uploadTask.task_id }}</span>
          <span>{{ progress }}%</span>
        </div>

        <div v-if="uploadTask.status === 'completed'" class="success-message">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
          <span>文档上传成功！</span>
        </div>

        <div v-if="uploadTask.status === 'failed'" class="error-message">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="15" y1="9" x2="9" y2="15"></line>
            <line x1="9" y1="9" x2="15" y2="15"></line>
          </svg>
          <span>上传失败，请重试</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import api from '../services/api'

const fileInput = ref(null)
const selectedFile = ref(null)
const isDragging = ref(false)
const isUploading = ref(false)
const uploadTask = ref(null)
const progress = ref(0)
let pollInterval = null

const statusText = computed(() => {
  if (!uploadTask.value) return ''
  const statusMap = {
    'pending': '等待中',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败'
  }
  return statusMap[uploadTask.value.status] || uploadTask.value.status
})

const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file) {
    selectedFile.value = file
  }
}

const handleDrop = (event) => {
  isDragging.value = false
  const file = event.dataTransfer.files[0]
  if (file) {
    selectedFile.value = file
  }
}

const removeFile = () => {
  selectedFile.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const startUpload = async () => {
  if (!selectedFile.value) return

  isUploading.value = true
  uploadTask.value = null
  progress.value = 0

  try {
    const response = await api.uploadFile(selectedFile.value)
    const taskIds = response.task_ids || []

    if (taskIds.length > 0) {
      uploadTask.value = {
        task_id: taskIds[0],
        status: 'processing'
      }
      startPolling(taskIds[0])
    } else {
      throw new Error('No task IDs returned')
    }
  } catch (error) {
    console.error('Upload error:', error)
    uploadTask.value = { status: 'failed' }
    isUploading.value = false
  }
}

const startPolling = (taskId) => {
  pollInterval = setInterval(async () => {
    try {
      const status = await api.getTaskStatus(taskId)
      uploadTask.value = {
        task_id: taskId,
        status: status.status
      }

      if (status.status === 'completed') {
        progress.value = 100
        stopPolling()
        isUploading.value = false
      } else if (status.status === 'failed') {
        stopPolling()
        isUploading.value = false
      } else {
        progress.value = Math.min(progress.value + 10, 90)
      }
    } catch (error) {
      console.error('Polling error:', error)
    }
  }, 2000)
}

const stopPolling = () => {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.import-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-primary);
}

.import-header {
  padding: 20px 32px;
  border-bottom: 1px solid var(--border-color);
}

.import-header h1 {
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

.import-content {
  flex: 1;
  padding: 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  max-width: 600px;
  margin: 0 auto;
  width: 100%;
}

.upload-area {
  width: 100%;
  border: 2px dashed var(--border-color);
  border-radius: 12px;
  padding: 48px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background: var(--bg-secondary);
}

.upload-area:hover,
.upload-area.dragging {
  border-color: var(--primary-color);
  background: rgba(79, 70, 229, 0.02);
}

.upload-area.has-file {
  padding: 24px;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.upload-icon {
  width: 72px;
  height: 72px;
  background: var(--bg-primary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
}

.upload-placeholder h3 {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
  margin: 0;
}

.upload-placeholder p {
  font-size: 13px;
  color: var(--text-tertiary);
  margin: 0;
}

.file-preview {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
}

.file-icon {
  width: 48px;
  height: 48px;
  background: var(--bg-primary);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary-color);
  flex-shrink: 0;
}

.file-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: left;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 12px;
  color: var(--text-tertiary);
}

.remove-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  border-radius: 6px;
  transition: all 0.2s;
}

.remove-btn:hover {
  background: #fee2e2;
  color: #dc2626;
}

.upload-btn {
  width: 100%;
  margin-top: 24px;
  padding: 14px 24px;
  background: var(--primary-color);
  color: white;
  border-radius: 8px;
  font-weight: 500;
  font-size: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: background 0.2s;
}

.upload-btn:hover:not(:disabled) {
  background: var(--primary-hover);
}

.upload-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.task-status {
  width: 100%;
  margin-top: 24px;
  padding: 20px;
  background: var(--bg-secondary);
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

.status-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.status-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.status-badge {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 20px;
  font-weight: 500;
}

.status-badge.pending {
  background: #fef3c7;
  color: #92400e;
}

.status-badge.processing {
  background: #dbeafe;
  color: #1e40af;
}

.status-badge.completed {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.failed {
  background: #fee2e2;
  color: #991b1b;
}

.progress-bar {
  height: 6px;
  background: var(--border-color);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 12px;
}

.progress-fill {
  height: 100%;
  background: var(--primary-color);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.status-details {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-tertiary);
}

.success-message,
.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 13px;
}

.success-message {
  background: #d1fae5;
  color: #065f46;
}

.error-message {
  background: #fee2e2;
  color: #991b1b;
}
</style>
