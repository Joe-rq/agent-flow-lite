import { ref, type Ref } from 'vue'
import { useSSEStream } from '@/composables/useSSEStream'
import { useToast } from '@/composables/useToast'
import { API_BASE } from '@/utils/constants'

export function useWorkflowExecution(currentWorkflowId: Ref<string | null>) {
  const { isStreaming: isRunning, fetchSSE } = useSSEStream()
  const runInput = ref('')
  const runOutput = ref('')
  const runLogs = ref<string[]>([])
  const showRunDialog = ref(false)
  const { showToast } = useToast()

  function showError(message: string) {
    showToast(message)
  }

  function appendRunLog(message: string) {
    runLogs.value.push(message)
  }

  function openRunDialog() {
    if (!currentWorkflowId.value) {
      showError('请先保存或加载工作流')
      return
    }
    runOutput.value = ''
    runLogs.value = []
    showRunDialog.value = true
  }

  function closeRunDialog() {
    if (isRunning.value) return
    showRunDialog.value = false
  }

  async function executeWorkflow() {
    if (!currentWorkflowId.value) {
      showError('请先保存或加载工作流')
      return
    }
    if (!runInput.value.trim()) {
      showError('请输入测试输入')
      return
    }
    runOutput.value = ''
    runLogs.value = []

    try {
      await fetchSSE({
        url: `${API_BASE}/workflows/${currentWorkflowId.value}/execute`,
        body: { input: runInput.value },
        onEvent: (eventType, data) => {
          if (eventType === 'token') {
            runOutput.value += (data.content as string) || ''
          } else if (eventType === 'workflow_start') {
            appendRunLog(`开始工作流: ${data.workflow_name || ''}`)
          } else if (eventType === 'node_start') {
            appendRunLog(`执行节点: ${data.node_type || ''}`)
          } else if (eventType === 'node_complete') {
            appendRunLog(`节点完成: ${data.node_id || ''}`)
          } else if (eventType === 'thought') {
            appendRunLog((data.content as string) || (data.status as string) || '处理中')
          } else if (eventType === 'workflow_complete') {
            appendRunLog('工作流执行完成')
            if (data.final_output) {
              runOutput.value = String(data.final_output)
            }
          } else if (eventType === 'workflow_error' || eventType === 'node_error') {
            appendRunLog(`错误: ${data.error || '未知错误'}`)
          } else if (eventType === 'done') {
            appendRunLog(`状态: ${data.status || 'complete'}`)
          }
        },
      })
    } catch (error) {
      console.error('执行工作流失败:', error)
      showError('执行工作流失败')
    }
  }

  return {
    isRunning, runInput, runOutput, runLogs, showRunDialog,
    openRunDialog, closeRunDialog, executeWorkflow,
  }
}
