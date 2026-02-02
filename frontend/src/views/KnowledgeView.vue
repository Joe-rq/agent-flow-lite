<template>
  <div class="knowledge-view">
    <div class="page-header">
      <h1>知识库管理</h1>
      <button class="btn-primary" @click="showCreateDialog = true">
        + 新建知识库
      </button>
    </div>

    <!-- 知识库列表 -->
    <div v-if="!selectedKB" class="kb-list">
      <div
        v-for="kb in knowledgeBases"
        :key="kb.id"
        class="kb-card"
        @click="selectKnowledgeBase(kb)"
      >
        <div class="kb-card-header">
          <h3 class="kb-name">{{ kb.name }}</h3>
          <span class="kb-doc-count">{{ kb.documentCount }} 文档</span>
        </div>
        <div class="kb-card-footer">
          <span class="kb-created">创建于 {{ formatDate(kb.createdAt) }}</span>
        </div>
      </div>

      <div v-if="knowledgeBases.length === 0" class="empty-state">
        <p>暂无知识库</p>
        <button class="btn-primary" @click="showCreateDialog = true">
          创建第一个知识库
        </button>
      </div>
    </div>

    <!-- 知识库详情 -->
    <div v-else class="kb-detail">
      <div class="kb-detail-header">
        <button class="btn-back" @click="selectedKB = null">← 返回列表</button>
        <h2>{{ selectedKB.name }}</h2>
        <span class="kb-meta">{{ documents.length }} 个文档</span>
      </div>

      <!-- 上传区域 -->
      <div
        class="upload-area"
        :class="{ dragging: isDragging }"
        @dragenter.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @dragover.prevent
        @drop.prevent="handleDrop"
        @click="triggerFileInput"
      >
        <input
          ref="fileInput"
          type="file"
          accept=".txt,.md"
          multiple
          style="display: none"
          @change="handleFileSelect"
        />
        <div class="upload-content">
          <div class="upload-icon">📄</div>
          <p class="upload-text">
            <span class="highlight">点击选择文件</span> 或拖拽文件到此处
          </p>
          <p class="upload-hint">支持 .txt, .md 格式</p>
        </div>
      </div>

      <!-- 上传进度列表 -->
      <div v-if="uploadTasks.length > 0" class="upload-tasks">
        <h3>上传进度</h3>
        <div
          v-for="task in uploadTasks"
          :key="task.id"
          class="upload-task-item"
          :class="task.status"
        >
          <div class="task-info">
            <span class="task-name">{{ task.fileName }}</span>
            <span class="task-size">{{ formatFileSize(task.fileSize) }}</span>
          </div>
          <div class="task-progress">
            <div class="progress-bar">
              <div
                class="progress-fill"
                :style="{ width: task.progress + '%' }"
              ></div>
            </div>
            <span class="task-status">{{ getStatusText(task.status) }}</span>
          </div>
        </div>
      </div>

      <!-- 检索测试区 -->
      <div class="search-section">
        <h3>检索测试</h3>
        <div class="search-box">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="输入查询内容测试检索效果..."
            class="search-input"
            @keyup.enter="performSearch"
          />
          <button
            class="btn-search"
            :disabled="!searchQuery.trim() || isSearching"
            @click="performSearch"
          >
            {{ isSearching ? '检索中...' : '检索' }}
          </button>
        </div>

        <!-- 检索结果 -->
        <div v-if="searchResults.length > 0" class="search-results">
          <div class="results-header">
            <span>找到 {{ searchResults.length }} 个相关片段</span>
          </div>
          <div
            v-for="(result, index) in searchResults"
            :key="index"
            class="result-item"
          >
            <div class="result-meta">
              <span class="result-index">#{{ index + 1 }}</span>
              <span class="result-score">相似度: {{ (result.score * 100).toFixed(1) }}%</span>
            </div>
            <div class="result-text">{{ result.text }}</div>
          </div>
        </div>

        <div v-if="searchError" class="search-error">
          {{ searchError }}
        </div>
      </div>

      <!-- 文档列表 -->
      <div class="document-list">
        <h3>文档列表</h3>
        <div v-if="documents.length === 0" class="empty-docs">
          <p>暂无文档，请上传文件</p>
        </div>
        <div v-else class="docs-table">
          <div class="docs-header">
            <span class="col-name">文件名</span>
            <span class="col-status">状态</span>
            <span class="col-size">大小</span>
            <span class="col-action">操作</span>
          </div>
          <div
            v-for="doc in documents"
            :key="doc.id"
            class="docs-row"
          >
            <span class="col-name" :title="doc.fileName">
              {{ doc.fileName }}
            </span>
            <span class="col-status">
              <span class="status-badge" :class="doc.status">
                {{ getDocStatusText(doc.status) }}
              </span>
            </span>
            <span class="col-size">{{ formatFileSize(doc.fileSize) }}</span>
            <span class="col-action">
              <button
                class="btn-delete"
                @click="deleteDocument(doc.id)"
                :disabled="doc.status === 'processing'"
              >
                删除
              </button>
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建知识库对话框 -->
    <div v-if="showCreateDialog" class="dialog-overlay" @click.self="showCreateDialog = false">
      <div class="dialog">
        <h3>新建知识库</h3>
        <div class="form-group">
          <label>知识库名称</label>
          <input
            v-model="newKBName"
            type="text"
            placeholder="请输入知识库名称"
            @keyup.enter="createKnowledgeBase"
          />
        </div>
        <div class="dialog-actions">
          <button class="btn-secondary" @click="showCreateDialog = false">
            取消
          </button>
          <button
            class="btn-primary"
            :disabled="!newKBName.trim()"
            @click="createKnowledgeBase"
          >
            创建
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

// 类型定义
interface KnowledgeBase {
  id: string
  name: string
  documentCount: number
  createdAt: string
}

interface Document {
  id: string
  fileName: string
  status: 'pending' | 'processing' | 'completed' | 'error'
  fileSize: number
  createdAt: string
}

interface UploadTask {
  id: string
  fileName: string
  fileSize: number
  progress: number
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error'
  file: File
}

interface SearchResult {
  text: string
  score: number
  metadata?: {
    doc_id?: string
    chunk_index?: number
  }
}

// 状态
const knowledgeBases = ref<KnowledgeBase[]>([])
const selectedKB = ref<KnowledgeBase | null>(null)
const documents = ref<Document[]>([])
const showCreateDialog = ref(false)
const newKBName = ref('')
const fileInput = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)
const uploadTasks = ref<UploadTask[]>([])

// 检索测试状态
const searchQuery = ref('')
const searchResults = ref<SearchResult[]>([])
const isSearching = ref(false)
const searchError = ref('')

// 轮询定时器
let pollInterval: number | null = null

// API 基础 URL
const API_BASE = '/api/v1'

// 格式化日期
function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
}

// 格式化文件大小
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 获取上传状态文本
function getStatusText(status: UploadTask['status']): string {
  const statusMap: Record<string, string> = {
    pending: '等待中',
    uploading: '上传中',
    processing: '处理中',
    completed: '完成',
    error: '失败',
  }
  return statusMap[status] || status
}

// 获取文档状态文本
function getDocStatusText(status: Document['status']): string {
  const statusMap: Record<string, string> = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    error: '失败',
  }
  return statusMap[status] || status
}

// 显示错误提示
function showError(message: string) {
  alert(message)
}

// 加载知识库列表
async function loadKnowledgeBases() {
  try {
    const response = await axios.get(`${API_BASE}/knowledge`)
    knowledgeBases.value = (response.data.items || []).map((kb: any) => ({
      id: kb.id,
      name: kb.name,
      documentCount: kb.document_count || 0,
      createdAt: kb.created_at,
    }))
  } catch (error) {
    console.error('加载知识库列表失败:', error)
    showError('加载知识库列表失败')
  }
}

// 选择知识库
async function selectKnowledgeBase(kb: KnowledgeBase) {
  selectedKB.value = kb
  await loadDocuments(kb.id)
  startPolling()
}

// 加载文档列表
async function loadDocuments(kbId: string) {
  try {
    const response = await axios.get(`${API_BASE}/knowledge/${kbId}/documents`)
    documents.value = (response.data.documents || []).map((doc: any) => ({
      id: doc.id,
      fileName: doc.filename,
      status: doc.status,
      fileSize: doc.file_size,
      createdAt: doc.created_at,
    }))
  } catch (error) {
    console.error('加载文档列表失败:', error)
    showError('加载文档列表失败')
    documents.value = []
  }
}

// 创建知识库
async function createKnowledgeBase() {
  if (!newKBName.value.trim()) return

  try {
    const response = await axios.post(`${API_BASE}/knowledge`, {
      name: newKBName.value.trim(),
    })
    const kb = response.data
    knowledgeBases.value.unshift({
      id: kb.id,
      name: kb.name,
      documentCount: kb.document_count || 0,
      createdAt: kb.created_at,
    })
    showCreateDialog.value = false
    newKBName.value = ''
  } catch (error) {
    console.error('创建知识库失败:', error)
    showError('创建知识库失败')
  }
}

// 触发文件选择
function triggerFileInput() {
  fileInput.value?.click()
}

// 处理文件选择
function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const files = target.files
  if (files) {
    handleFiles(Array.from(files))
  }
  // 重置 input 以便可以再次选择相同文件
  target.value = ''
}

// 处理拖拽
function handleDrop(event: DragEvent) {
  isDragging.value = false
  const files = event.dataTransfer?.files
  if (files) {
    const validFiles = Array.from(files).filter(file =>
      file.name.endsWith('.txt') || file.name.endsWith('.md')
    )
    handleFiles(validFiles)
  }
}

// 处理文件上传
async function handleFiles(files: File[]) {
  if (!selectedKB.value) return

  for (const file of files) {
    const task: UploadTask = {
      id: 'task-' + Date.now() + Math.random(),
      fileName: file.name,
      fileSize: file.size,
      progress: 0,
      status: 'pending',
      file,
    }
    uploadTasks.value.push(task)

    // 开始上传
    await uploadFile(task)
  }
}

// 上传单个文件
async function uploadFile(task: UploadTask) {
  if (!selectedKB.value) return

  task.status = 'uploading'

  const formData = new FormData()
  formData.append('file', task.file)

  try {
    const response = await axios.post(
      `${API_BASE}/knowledge/${selectedKB.value.id}/upload`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            task.progress = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            )
          }
        },
      }
    )

    task.status = 'processing'
    task.progress = 100

    // 刷新文档列表
    await loadDocuments(selectedKB.value.id)

    // 模拟处理完成（实际应该轮询状态）
    setTimeout(() => {
      task.status = 'completed'
    }, 2000)
  } catch (error: any) {
    console.error('上传失败:', error)
    task.status = 'error'
    showError(error.response?.data?.detail || '上传失败')
  }
}

// 删除文档
async function deleteDocument(docId: string) {
  if (!selectedKB.value) return

  if (!confirm('确定要删除这个文档吗？')) return

  try {
    await axios.delete(
      `${API_BASE}/knowledge/${selectedKB.value.id}/documents/${docId}`
    )
    documents.value = documents.value.filter(doc => doc.id !== docId)
  } catch (error) {
    console.error('删除文档失败:', error)
    showError('删除文档失败')
  }
}

// 执行检索
async function performSearch() {
  if (!selectedKB.value || !searchQuery.value.trim()) return

  isSearching.value = true
  searchError.value = ''
  searchResults.value = []

  try {
    const response = await axios.get(
      `${API_BASE}/knowledge/${selectedKB.value.id}/search`,
      {
        params: {
          query: searchQuery.value.trim(),
          top_k: 5
        }
      }
    )
    searchResults.value = response.data.results || []
  } catch (error: any) {
    console.error('检索失败:', error)
    searchError.value = error.response?.data?.detail || '检索失败，请重试'
  } finally {
    isSearching.value = false
  }
}

// 轮询文档状态
function startPolling() {
  stopPolling()
  pollInterval = window.setInterval(async () => {
    if (selectedKB.value) {
      await loadDocuments(selectedKB.value.id)
    }
  }, 5000) // 每5秒轮询一次
}

function stopPolling() {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

// 生命周期
onMounted(() => {
  loadKnowledgeBases()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.knowledge-view {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
}

/* 按钮样式 */
.btn-primary {
  background-color: #2c3e50;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background-color: #34495e;
}

.btn-primary:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: #ecf0f1;
  color: #2c3e50;
  border: 1px solid #bdc3c7;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background-color: #d5dbdb;
}

.btn-back {
  background: none;
  border: none;
  color: #3498db;
  cursor: pointer;
  font-size: 14px;
  padding: 0;
  margin-bottom: 8px;
}

.btn-back:hover {
  text-decoration: underline;
}

.btn-delete {
  background-color: #e74c3c;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-delete:hover:not(:disabled) {
  background-color: #c0392b;
}

.btn-delete:disabled {
  background-color: #bdc3c7;
  cursor: not-allowed;
}

/* 知识库列表 */
.kb-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.kb-card {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
}

.kb-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #3498db;
}

.kb-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.kb-name {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
}

.kb-doc-count {
  background-color: #ecf0f1;
  color: #7f8c8d;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
}

.kb-card-footer {
  color: #95a5a6;
  font-size: 13px;
}

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 60px 20px;
  color: #7f8c8d;
}

.empty-state p {
  margin-bottom: 20px;
  font-size: 16px;
}

/* 知识库详情 */
.kb-detail {
  background: white;
  border-radius: 8px;
  padding: 24px;
}

.kb-detail-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e9ecef;
}

.kb-detail-header h2 {
  margin: 8px 0;
  font-size: 22px;
  color: #2c3e50;
}

.kb-meta {
  color: #7f8c8d;
  font-size: 14px;
}

/* 上传区域 */
.upload-area {
  border: 2px dashed #bdc3c7;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 24px;
}

.upload-area:hover,
.upload-area.dragging {
  border-color: #3498db;
  background-color: #f8f9fa;
}

.upload-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.upload-text {
  font-size: 16px;
  color: #2c3e50;
  margin: 0 0 8px 0;
}

.upload-text .highlight {
  color: #3498db;
  font-weight: 500;
}

.upload-hint {
  font-size: 13px;
  color: #95a5a6;
  margin: 0;
}

/* 上传任务列表 */
.upload-tasks {
  margin-bottom: 24px;
}

.upload-tasks h3 {
  font-size: 16px;
  color: #2c3e50;
  margin-bottom: 12px;
}

.upload-task-item {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 12px 16px;
  margin-bottom: 8px;
}

.upload-task-item.completed {
  background: #e8f5e9;
}

.upload-task-item.error {
  background: #ffebee;
}

.task-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.task-name {
  font-weight: 500;
  color: #2c3e50;
}

.task-size {
  color: #7f8c8d;
  font-size: 13px;
}

.task-progress {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background-color: #e9ecef;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: #3498db;
  transition: width 0.3s;
}

.task-status {
  font-size: 12px;
  color: #7f8c8d;
  min-width: 60px;
  text-align: right;
}

/* 文档列表 */
.document-list h3 {
  font-size: 16px;
  color: #2c3e50;
  margin-bottom: 12px;
}

.empty-docs {
  text-align: center;
  padding: 40px;
  color: #95a5a6;
  background: #f8f9fa;
  border-radius: 6px;
}

.docs-table {
  border: 1px solid #e9ecef;
  border-radius: 8px;
  overflow: hidden;
}

.docs-header,
.docs-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 100px;
  gap: 16px;
  padding: 12px 16px;
  align-items: center;
}

.docs-header {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #2c3e50;
  font-size: 14px;
}

.docs-row {
  border-top: 1px solid #e9ecef;
  font-size: 14px;
}

.docs-row:hover {
  background-color: #f8f9fa;
}

.col-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #2c3e50;
}

.col-status {
  display: flex;
}

.status-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.pending {
  background-color: #fff3e0;
  color: #e65100;
}

.status-badge.processing {
  background-color: #e3f2fd;
  color: #1565c0;
}

.status-badge.completed {
  background-color: #e8f5e9;
  color: #2e7d32;
}

.status-badge.error {
  background-color: #ffebee;
  color: #c62828;
}

.col-size {
  color: #7f8c8d;
}

/* 对话框 */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: white;
  border-radius: 8px;
  padding: 24px;
  width: 400px;
  max-width: 90vw;
}

.dialog h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  color: #2c3e50;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: #2c3e50;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #bdc3c7;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-group input:focus {
  outline: none;
  border-color: #3498db;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 检索测试区 */
.search-section {
  margin-bottom: 24px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.search-section h3 {
  font-size: 16px;
  color: #2c3e50;
  margin-bottom: 16px;
}

.search-box {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.search-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #bdc3c7;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.search-input:focus {
  border-color: #3498db;
}

.btn-search {
  padding: 12px 24px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-search:hover:not(:disabled) {
  background-color: #2980b9;
}

.btn-search:disabled {
  background-color: #bdc3c7;
  cursor: not-allowed;
}

.search-results {
  margin-top: 16px;
}

.results-header {
  font-size: 14px;
  color: #7f8c8d;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e9ecef;
}

.result-item {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 12px;
}

.result-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
}

.result-index {
  font-weight: 600;
  color: #3498db;
}

.result-score {
  color: #27ae60;
  font-weight: 500;
}

.result-text {
  font-size: 14px;
  color: #2c3e50;
  line-height: 1.6;
  max-height: 120px;
  overflow-y: auto;
}

.search-error {
  color: #e74c3c;
  font-size: 14px;
  padding: 12px;
  background: #ffebee;
  border-radius: 6px;
}
</style>
