import { ref, onMounted, onUnmounted } from 'vue'
import type { Ref } from 'vue'
import axios from 'axios'
import { API_BASE } from '@/utils/constants'
import type { KnowledgeBase, Document, UploadTask, SearchResult } from '@/types'

export function useKnowledgeApi(fileInput: Ref<HTMLInputElement | null>) {
  const knowledgeBases = ref<KnowledgeBase[]>([])
  const selectedKB = ref<KnowledgeBase | null>(null)
  const documents = ref<Document[]>([])
  const showCreateDialog = ref(false)
  const newKBName = ref('')
  const isDragging = ref(false)
  const uploadTasks = ref<UploadTask[]>([])

  const searchQuery = ref('')
  const searchResults = ref<SearchResult[]>([])
  const isSearching = ref(false)
  const searchError = ref('')

  let pollInterval: number | null = null

  function isSupportedFile(fileName: string): boolean {
    const lower = fileName.toLowerCase()
    return lower.endsWith('.txt') || lower.endsWith('.md') || lower.endsWith('.pdf') || lower.endsWith('.docx')
  }

  function getStatusText(status: UploadTask['status']): string {
    const map: Record<string, string> = {
      pending: '等待中', uploading: '上传中', processing: '处理中',
      completed: '完成', failed: '失败',
    }
    return map[status] || status
  }

  function getDocStatusText(status: Document['status']): string {
    const map: Record<string, string> = {
      pending: '待处理', processing: '处理中', completed: '已完成', failed: '失败',
    }
    return map[status] || status
  }

  function showError(message: string) {
    alert(message)
  }

  async function loadKnowledgeBases() {
    try {
      const res = await axios.get(`${API_BASE}/knowledge`)
      knowledgeBases.value = (res.data.items || []).map(
        (kb: { id: string; name: string; document_count?: number; created_at: string }) => ({
          id: kb.id, name: kb.name,
          documentCount: kb.document_count || 0, createdAt: kb.created_at,
        }),
      )
    } catch { showError('加载知识库列表失败') }
  }

  async function loadDocuments(kbId: string) {
    try {
      const res = await axios.get(`${API_BASE}/knowledge/${kbId}/documents`)
      documents.value = (res.data.documents || []).map(
        (d: { id: string; filename: string; status: string; file_size: number; created_at: string }) => ({
          id: d.id, fileName: d.filename, status: d.status,
          fileSize: d.file_size, createdAt: d.created_at,
        }),
      )
    } catch { showError('加载文档列表失败'); documents.value = [] }
  }

  async function selectKnowledgeBase(kb: KnowledgeBase) {
    selectedKB.value = kb
    await loadDocuments(kb.id)
    startPolling()
  }

  async function createKnowledgeBase() {
    if (!newKBName.value.trim()) return
    try {
      const res = await axios.post(`${API_BASE}/knowledge`, { name: newKBName.value.trim() })
      const kb = res.data
      knowledgeBases.value.unshift({
        id: kb.id, name: kb.name,
        documentCount: kb.document_count || 0, createdAt: kb.created_at,
      })
      showCreateDialog.value = false
      newKBName.value = ''
    } catch { showError('创建知识库失败') }
  }

  async function deleteKnowledgeBase(kbId: string, kbName: string) {
    if (!confirm(`确定要删除知识库「${kbName}」吗？所有文档和向量数据将被永久删除。`)) return
    try {
      await axios.delete(`${API_BASE}/knowledge/${kbId}`)
      knowledgeBases.value = knowledgeBases.value.filter(kb => kb.id !== kbId)
    } catch { showError('删除知识库失败') }
  }

  async function deleteDocument(docId: string) {
    if (!selectedKB.value) return
    if (!confirm('确定要删除这个文档吗？')) return
    try {
      await axios.delete(`${API_BASE}/knowledge/${selectedKB.value.id}/documents/${docId}`)
      documents.value = documents.value.filter(doc => doc.id !== docId)
    } catch { showError('删除文档失败') }
  }

  function triggerFileInput() { fileInput.value?.click() }

  function handleFileSelect(event: Event) {
    const target = event.target as HTMLInputElement
    if (target.files) {
      const files = Array.from(target.files)
      const validFiles = files.filter((f) => isSupportedFile(f.name))
      if (validFiles.length !== files.length) {
        showError('仅支持 .txt、.md、.pdf、.docx 文件')
      }
      handleFiles(validFiles)
    }
    target.value = ''
  }

  function handleDrop(event: DragEvent) {
    isDragging.value = false
    const files = event.dataTransfer?.files
    if (files) {
      handleFiles(Array.from(files).filter((f) => isSupportedFile(f.name)))
    }
  }

  async function handleFiles(files: File[]) {
    if (!selectedKB.value) return
    for (const file of files) {
      const task: UploadTask = {
        id: 'task-' + Date.now() + Math.random(),
        fileName: file.name, fileSize: file.size,
        progress: 0, status: 'pending', file,
      }
      uploadTasks.value.push(task)
      await uploadFile(task)
    }
  }

  async function uploadFile(task: UploadTask) {
    if (!selectedKB.value) return
    task.status = 'uploading'
    const formData = new FormData()
    formData.append('file', task.file)
    try {
      await axios.post(`${API_BASE}/knowledge/${selectedKB.value.id}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => {
          if (e.total) task.progress = Math.round((e.loaded * 100) / e.total)
        },
      })
      task.status = 'processing'
      task.progress = 100
      await loadDocuments(selectedKB.value!.id)
      setTimeout(() => { task.status = 'completed' }, 2000)
    } catch (error) {
      task.status = 'failed'
      const err = error as { response?: { data?: { detail?: string } } }
      showError(err.response?.data?.detail || '上传失败')
    }
  }

  async function performSearch() {
    if (!selectedKB.value || !searchQuery.value.trim()) return
    isSearching.value = true
    searchError.value = ''
    searchResults.value = []
    try {
      const res = await axios.get(`${API_BASE}/knowledge/${selectedKB.value.id}/search`, {
        params: { query: searchQuery.value.trim(), top_k: 5 },
      })
      searchResults.value = res.data.results || []
    } catch (error) {
      const err = error as { response?: { data?: { detail?: string } } }
      searchError.value = err.response?.data?.detail || '检索失败，请重试'
    } finally { isSearching.value = false }
  }

  function startPolling() {
    stopPolling()
    pollInterval = window.setInterval(async () => {
      if (selectedKB.value) await loadDocuments(selectedKB.value.id)
    }, 5000)
  }

  function stopPolling() {
    if (pollInterval) { clearInterval(pollInterval); pollInterval = null }
  }

  onMounted(() => { loadKnowledgeBases() })
  onUnmounted(() => { stopPolling() })

  return {
    knowledgeBases, selectedKB, documents, showCreateDialog, newKBName,
    isDragging, uploadTasks, searchQuery, searchResults, isSearching, searchError,
    getStatusText, getDocStatusText,
    loadKnowledgeBases, selectKnowledgeBase, loadDocuments,
    createKnowledgeBase, deleteKnowledgeBase, deleteDocument,
    triggerFileInput, handleFileSelect, handleDrop,
    performSearch,
  }
}
