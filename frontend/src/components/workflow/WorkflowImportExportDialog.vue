<template>
  <div v-if="visible" class="dialog-overlay" @click.self="close">
    <div class="dialog dialog--wide">
      <h3>{{ mode === 'export' ? '导出工作流' : '导入工作流' }}</h3>
      
      <!-- Export Mode -->
      <div v-if="mode === 'export'" class="dialog-content">
        <div v-if="isExporting" class="status-message">
          正在导出...
        </div>
        <div v-else-if="exportError" class="status-message status-error">
          导出失败: {{ exportError }}
        </div>
        <div v-else-if="exportData" class="export-section">
          <p class="hint-text">工作流 JSON 已准备好，点击下方按钮下载或复制：</p>
          <textarea
            ref="exportTextarea"
            v-model="exportDataJson"
            readonly
            class="json-textarea"
            rows="12"
          />
          <div class="dialog-actions">
            <Button variant="outline" size="sm" @click="copyToClipboard">
              {{ copied ? '已复制!' : '复制到剪贴板' }}
            </Button>
            <Button variant="default" size="sm" @click="downloadJson">
              下载 JSON 文件
            </Button>
            <Button variant="outline" size="sm" @click="close">关闭</Button>
          </div>
        </div>
        <div v-else class="status-message">
          准备导出...
        </div>
      </div>
      
      <!-- Import Mode -->
      <div v-else class="dialog-content">
        <!-- Template Section -->
        <div class="template-section">
          <p class="template-label">模板</p>
          <div class="template-buttons">
            <Button
              variant="outline"
              size="sm"
              :disabled="isImporting"
              @click="importTemplate('kb_qa')"
            >
              导入模板：知识库问答
            </Button>
            <Button
              variant="outline"
              size="sm"
              :disabled="isImporting"
              @click="importTemplate('sop_assistant')"
            >
              导入模板：SOP 助手
            </Button>
          </div>
        </div>

        <div class="import-tabs">
          <button
            :class="['tab-btn', { active: importTab === 'paste' }]"
            @click="importTab = 'paste'"
          >
            粘贴 JSON
          </button>
          <button
            :class="['tab-btn', { active: importTab === 'file' }]"
            @click="importTab = 'file'"
          >
            上传文件
          </button>
        </div>
        
        <!-- Paste Tab -->
        <div v-if="importTab === 'paste'" class="import-section">
          <textarea
            v-model="importJson"
            placeholder="在此粘贴工作流 JSON..."
            class="json-textarea"
            rows="10"
            :disabled="isImporting"
          />
        </div>
        
        <!-- File Tab -->
        <div v-else class="import-section">
          <div class="file-upload-area" @click="triggerFileInput" @drop.prevent="handleDrop" @dragover.prevent>
            <input
              ref="fileInput"
              type="file"
              accept=".json"
              class="hidden-input"
              @change="handleFileChange"
            />
            <p v-if="!selectedFile">点击或拖拽 JSON 文件到此处</p>
            <p v-else class="selected-file">已选择: {{ selectedFile.name }}</p>
          </div>
        </div>
        
        <div v-if="importError" class="status-message status-error">
          {{ importError }}
        </div>
        
        <div class="dialog-actions">
          <Button variant="default" size="sm" :disabled="!canImport || isImporting" @click="doImport">
            {{ isImporting ? '导入中...' : '导入' }}
          </Button>
          <Button variant="outline" size="sm" :disabled="isImporting" @click="close">
            取消
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import Button from '@/components/ui/Button.vue'
import { getTemplateBySlug, type TemplateSlug } from '@/composables/workflow/workflowTemplates'
import { useToast } from '@/composables/useToast'

interface ExportPayload {
  version: number
  workflow: {
    name: string
    description: string
    graph_data: {
      nodes: any[]
      edges: any[]
    }
  }
}

interface ImportResult {
  id: string
  name: string
  description: string
  graph_data: {
    nodes: any[]
    edges: any[]
  }
}

const props = defineProps<{
  visible: boolean
  mode: 'export' | 'import'
  exportData: ExportPayload | null
  isExporting: boolean
  exportError: string | null
  isImporting: boolean
  importError: string | null
}>()

const emit = defineEmits<{
  close: []
  import: [data: ExportPayload]
  importTemplate: [data: ExportPayload, templateName: string]
}>()

const importTab = ref<'paste' | 'file'>('paste')
const importJson = ref('')
const selectedFile = ref<File | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const exportTextarea = ref<HTMLTextAreaElement | null>(null)
const copied = ref(false)

const { showToast } = useToast()

const exportDataJson = computed(() => {
  if (!props.exportData) return ''
  return JSON.stringify(props.exportData, null, 2)
})

const canImport = computed(() => {
  if (props.isImporting) return false
  if (importTab.value === 'paste') {
    return importJson.value.trim().length > 0
  }
  return selectedFile.value !== null
})

watch(() => props.visible, (visible) => {
  if (visible) {
    // Reset state when opening
    importJson.value = ''
    selectedFile.value = null
    importTab.value = 'paste'
    copied.value = false
  }
})

function close() {
  emit('close')
}

function copyToClipboard() {
  if (!exportTextarea.value) return
  exportTextarea.value.select()
  document.execCommand('copy')
  copied.value = true
  setTimeout(() => {
    copied.value = false
  }, 2000)
}

function downloadJson() {
  if (!props.exportData) return
  const blob = new Blob([exportDataJson.value], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  const filename = props.exportData.workflow.name
    ? `${props.exportData.workflow.name.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_')}.json`
    : 'workflow.json'
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    selectedFile.value = file
    readFile(file)
  }
}

function handleDrop(event: DragEvent) {
  const file = event.dataTransfer?.files[0]
  if (file && file.name.endsWith('.json')) {
    selectedFile.value = file
    readFile(file)
  }
}

function readFile(file: File) {
  const reader = new FileReader()
  reader.onload = (e) => {
    importJson.value = e.target?.result as string
  }
  reader.readAsText(file)
}

function doImport() {
  let data: ExportPayload
  try {
    data = JSON.parse(importJson.value)
  } catch (e) {
    // Validation happens in parent, but we can pre-check
    showToast('JSON 格式无效，请检查输入', 'warning')
    return
  }
  emit('import', data)
}

function importTemplate(slug: TemplateSlug) {
  const template = getTemplateBySlug(slug)
  emit('importTemplate', template, slug)
}
</script>

<style scoped>
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
  max-height: 80vh;
  overflow-y: auto;
}

.dialog--wide {
  width: 600px;
}

.dialog h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: var(--color-foreground);
}

.dialog-content {
  min-height: 200px;
}

.hint-text {
  color: var(--color-muted-foreground);
  font-size: 14px;
  margin-bottom: 12px;
}

.json-textarea {
  width: 100%;
  min-height: 200px;
  padding: 12px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.5;
  resize: vertical;
  background: var(--color-card);
  color: var(--color-foreground);
}

.json-textarea:focus {
  outline: none;
  border-color: var(--color-primary);
}

.json-textarea:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.import-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.tab-btn {
  padding: 8px 16px;
  border: 1px solid var(--color-border);
  background: var(--color-muted);
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: var(--color-card);
}

.tab-btn.active {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.file-upload-area {
  border: 2px dashed var(--color-border);
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-upload-area:hover {
  border-color: var(--color-primary);
  background: var(--color-card);
}

.hidden-input {
  display: none;
}

.selected-file {
  color: var(--color-primary);
  font-weight: 500;
}

.status-message {
  text-align: center;
  padding: 40px 20px;
  color: var(--color-muted-foreground);
}

.status-error {
  color: #dc2626;
  background: #fef2f2;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 16px;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}

.export-section,
.import-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.template-section {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-border);
}

.template-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-muted-foreground);
  margin: 0 0 12px 0;
}

.template-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.template-btn {
  padding: 8px 16px;
  border: 1px solid var(--color-border);
  background: var(--color-muted);
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  color: var(--color-foreground);
}

.template-btn:hover:not(:disabled) {
  background: var(--color-card);
  border-color: var(--color-primary);
}

.template-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
