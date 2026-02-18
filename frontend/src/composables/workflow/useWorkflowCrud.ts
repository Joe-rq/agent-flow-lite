import { ref } from 'vue'
import axios from 'axios'
import { API_BASE } from '@/utils/constants'
import { useToast } from '@/composables/useToast'
import { useConfirmDialog } from '@/composables/useConfirmDialog'

export interface WorkflowItem {
  id: string
  name: string
  created_at: string
}

export interface ExportPayload {
  version: number
  workflow: {
    name: string
    description: string
    graph_data: {
      nodes: GraphNode[]
      edges: GraphEdge[]
    }
  }
}

interface GraphNode {
  id: string
  type: string
  position: { x: number; y: number }
  label?: string
  data?: Record<string, unknown>
}

interface GraphEdge {
  id: string
  source: string
  target: string
  sourceHandle?: string | null
  targetHandle?: string | null
}

  
export function useWorkflowCrud(
  toObject: () => { nodes: any[]; edges: any[] },
  setNodes: (nodes: any[]) => void,
  setEdges: (edges: any[]) => void,
) {
  const isSaving = ref(false)
  const showLoadDialog = ref(false)
  const workflows = ref<WorkflowItem[]>([])
  const currentWorkflowId = ref<string | null>(null)
  const currentWorkflowName = ref('')
  
  const showImportExportDialog = ref(false)
  const importExportMode = ref<'export' | 'import'>('export')
  const exportData = ref<ExportPayload | null>(null)
  const isExporting = ref(false)
  const exportError = ref<string | null>(null)
  const isImporting = ref(false)
  const importError = ref<string | null>(null)

  const { showToast } = useToast()
  const { confirmDialog } = useConfirmDialog()

  function showError(message: string) {
    showToast(message)
  }

  function getDefaultLabel(type: string): string {
    const labels: Record<string, string> = {
      start: '开始', llm: 'LLM', knowledge: '知识库',
      end: '结束', condition: '条件', skill: '技能',
    }
    return labels[type] || type
  }

  async function saveWorkflow() {
    if (isSaving.value) return
    const isUpdate = !!currentWorkflowId.value
    let workflowName = currentWorkflowName.value
    if (!isUpdate) {
      workflowName = prompt('请输入工作流名称:', '新建工作流') || ''
      if (!workflowName) return
    }
    isSaving.value = true
    try {
      const flowData = toObject()
      const graphData = {
        nodes: flowData.nodes.map((n) => ({
          id: n.id, type: n.type, position: n.position,
          label: n.label, data: n.data || {},
        })),
        edges: flowData.edges.map((e) => ({
          id: e.id, source: e.source, target: e.target,
          sourceHandle: e.sourceHandle, targetHandle: e.targetHandle,
        })),
      }
      const payload = { name: workflowName, description: '', graph_data: graphData }
      if (isUpdate) {
        await axios.put(`${API_BASE}/workflows/${currentWorkflowId.value}`, payload)
        showError('工作流更新成功！')
      } else {
        const response = await axios.post(`${API_BASE}/workflows`, payload)
        currentWorkflowId.value = response.data.id
        currentWorkflowName.value = response.data.name
        showError('工作流保存成功！')
      }
    } catch (error) {
      console.error('保存工作流失败:', error)
      showError('保存工作流失败')
    } finally {
      isSaving.value = false
    }
  }

  async function loadWorkflows() {
    try {
      const response = await axios.get(`${API_BASE}/workflows`)
      workflows.value = response.data.items || []
      showLoadDialog.value = true
    } catch (error) {
      console.error('加载工作流列表失败:', error)
      showError('加载工作流列表失败')
    }
  }

  async function deleteWorkflow() {
    if (!currentWorkflowId.value) {
      showError('请先加载一个工作流')
      return
    }
    if (!(await confirmDialog(`确定要删除工作流「${currentWorkflowName.value}」吗？此操作不可恢复。`))) return
    try {
      await axios.delete(`${API_BASE}/workflows/${currentWorkflowId.value}`)
      showError('工作流删除成功！')
      currentWorkflowId.value = null
      currentWorkflowName.value = ''
      setNodes([{ id: '1', type: 'start', label: '开始', position: { x: 100, y: 100 } }])
      setEdges([])
    } catch (error) {
      console.error('删除工作流失败:', error)
      showError('删除工作流失败')
    }
  }

  async function loadWorkflow(workflowId: string) {
    try {
      const response = await axios.get(`${API_BASE}/workflows/${workflowId}`)
      const workflow = response.data
      const graphData = workflow.graph_data
      if (graphData?.nodes) {
        setNodes(graphData.nodes.map((n: GraphNode) => ({
          id: n.id, type: n.type, position: n.position,
          label: n.label || getDefaultLabel(n.type), data: n.data || {},
        })))
      }
      if (graphData?.edges) {
        setEdges(graphData.edges.map((e: GraphEdge) => ({
          id: e.id, source: e.source, target: e.target,
          sourceHandle: e.sourceHandle, targetHandle: e.targetHandle,
        })))
      }
      currentWorkflowId.value = workflow.id
      currentWorkflowName.value = workflow.name
      showLoadDialog.value = false
      showError('工作流加载成功！')
    } catch (error) {
      console.error('加载工作流失败:', error)
      showError('加载工作流失败')
    }
  }

  function openExportDialog() {
    importExportMode.value = 'export'
    exportData.value = null
    exportError.value = null
    showImportExportDialog.value = true
    if (currentWorkflowId.value) {
      fetchExportData(currentWorkflowId.value)
    }
  }

  function openImportDialog() {
    importExportMode.value = 'import'
    importError.value = null
    showImportExportDialog.value = true
  }

  function closeImportExportDialog() {
    showImportExportDialog.value = false
    exportData.value = null
    exportError.value = null
    importError.value = null
  }

  async function fetchExportData(workflowId: string) {
    isExporting.value = true
    exportError.value = null
    try {
      const response = await axios.get(`${API_BASE}/workflows/${workflowId}/export`)
      exportData.value = response.data
    } catch (error) {
      console.error('导出工作流失败:', error)
      exportError.value = '导出失败，请重试'
    } finally {
      isExporting.value = false
    }
  }

  async function importWorkflow(data: ExportPayload, templateName?: string) {
    isImporting.value = true
    importError.value = null
    try {
      const headers: Record<string, string> = {}
      if (templateName) {
        headers['X-Template-Name'] = templateName
      }
      const response = await axios.post(`${API_BASE}/workflows/import`, data, { headers })
      const workflow = response.data
      const graphData = workflow.graph_data
      if (graphData?.nodes) {
        setNodes(graphData.nodes.map((n: GraphNode) => ({
          id: n.id, type: n.type, position: n.position,
          label: n.label || getDefaultLabel(n.type), data: n.data || {},
        })))
      }
      if (graphData?.edges) {
        setEdges(graphData.edges.map((e: GraphEdge) => ({
          id: e.id, source: e.source, target: e.target,
          sourceHandle: e.sourceHandle, targetHandle: e.targetHandle,
        })))
      }
      currentWorkflowId.value = workflow.id
      currentWorkflowName.value = workflow.name
      showImportExportDialog.value = false
      showError('工作流导入成功！')
    } catch (error) {
      console.error('导入工作流失败:', error)
      importError.value = '导入失败，请检查 JSON 格式是否正确'
    } finally {
      isImporting.value = false
    }
  }

  return {
    isSaving, showLoadDialog, workflows,
    currentWorkflowId, currentWorkflowName,
    saveWorkflow, loadWorkflows, deleteWorkflow, loadWorkflow,
    showImportExportDialog, importExportMode, exportData,
    isExporting, exportError, isImporting, importError,
    openExportDialog, openImportDialog, closeImportExportDialog,
    importWorkflow,
  }
}
