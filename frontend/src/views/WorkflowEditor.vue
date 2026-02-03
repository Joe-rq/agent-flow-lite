<template>
  <div class="workflow-editor">
    <!-- 顶部工具栏 -->
    <div class="workflow-toolbar">
      <div class="toolbar-left">
        <h2>工作流编辑器</h2>
      </div>
      <div class="toolbar-right">
        <Button variant="primary" size="sm" @click="saveWorkflow" :disabled="isSaving">
          {{ isSaving ? '保存中...' : '保存工作流' }}
        </Button>
        <Button variant="secondary" size="sm" @click="loadWorkflows">加载工作流</Button>
        <Button variant="primary" size="sm" @click="openRunDialog" :disabled="isRunning">
          {{ isRunning ? '运行中...' : '运行工作流' }}
        </Button>
        <Button variant="danger" size="sm" @click="deleteWorkflow" :disabled="!currentWorkflowId">
          删除工作流
        </Button>
        <Button variant="secondary" size="sm" @click="autoLayout">⚡ 自动布局</Button>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="editor-main">
      <!-- Vue Flow 画布 -->
      <div class="canvas-container">
      <VueFlow
        v-model="elements"
        :default-zoom="1"
        :min-zoom="0.2"
        :max-zoom="4"
        :default-edge-options="{ type: 'smoothstep', animated: true }"
        :delete-key-code="'Delete'"
        :snap-to-grid="true"
        :snap-grid="[20, 20]"
        @dragover="onDragOver"
        @drop="onDrop"
        @node-click="onNodeClick"
        @edge-click="onEdgeClick"
        @connect="onConnect"
        fit-view-on-init
      >
        <!-- 背景 -->
        <Background pattern-color="#e5e7eb" :gap="20" />

        <!-- 控制按钮 -->
        <Controls />

        <!-- 自定义节点 -->
        <template #node-start="props">
          <StartNode v-bind="props" />
          <Handle type="source" :position="Position.Right" />
        </template>

        <template #node-llm="props">
          <LLMNode v-bind="props" />
          <Handle type="target" :position="Position.Left" />
          <Handle type="source" :position="Position.Right" />
        </template>

        <template #node-knowledge="props">
          <KnowledgeNode v-bind="props" />
          <Handle type="target" :position="Position.Left" />
          <Handle type="source" :position="Position.Right" />
        </template>

        <template #node-end="props">
          <EndNode v-bind="props" />
        </template>

        <template #node-condition="props">
          <ConditionNode v-bind="props" />
        </template>
      </VueFlow>

      <!-- 抽屉切换按钮 -->
      <button
        class="drawer-toggle"
        :class="{ 'drawer-open': drawerOpen }"
        @click="drawerOpen = !drawerOpen"
        :title="drawerOpen ? '收起面板' : '展开面板'"
      >
        <span class="toggle-icon">{{ drawerOpen ? '▶' : '◀' }}</span>
      </button>

      <!-- 节点创建抽屉 -->
      <div class="node-drawer" :class="{ open: drawerOpen }">
        <h3 class="drawer-title">添加节点</h3>
        <div class="drawer-content">
          <div
            class="drawer-node-item"
            draggable="true"
            @dragstart="onDragStart($event, 'start')"
            @click="addNodeFromPanel('start')"
          >
            <span class="drawer-node-icon">▶</span>
            <span class="drawer-node-label">开始节点</span>
          </div>
          <div
            class="drawer-node-item"
            draggable="true"
            @dragstart="onDragStart($event, 'llm')"
            @click="addNodeFromPanel('llm')"
          >
            <span class="drawer-node-icon">🤖</span>
            <span class="drawer-node-label">LLM 节点</span>
          </div>
          <div
            class="drawer-node-item"
            draggable="true"
            @dragstart="onDragStart($event, 'knowledge')"
            @click="addNodeFromPanel('knowledge')"
          >
            <span class="drawer-node-icon">📚</span>
            <span class="drawer-node-label">知识库节点</span>
          </div>
          <div
            class="drawer-node-item"
            draggable="true"
            @dragstart="onDragStart($event, 'condition')"
            @click="addNodeFromPanel('condition')"
          >
            <span class="drawer-node-icon">⚡</span>
            <span class="drawer-node-label">条件节点</span>
          </div>
          <div
            class="drawer-node-item"
            draggable="true"
            @dragstart="onDragStart($event, 'end')"
            @click="addNodeFromPanel('end')"
          >
            <span class="drawer-node-icon">⏹</span>
            <span class="drawer-node-label">结束节点</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 加载工作流对话框 -->
  <div v-if="showLoadDialog" class="dialog-overlay" @click.self="showLoadDialog = false">
    <div class="dialog">
      <h3>加载工作流</h3>
      <div v-if="workflows.length === 0" class="empty-dialog">
        <p>暂无保存的工作流</p>
      </div>
      <div v-else class="workflow-list">
        <div
          v-for="workflow in workflows"
          :key="workflow.id"
          class="workflow-item"
          @click="loadWorkflow(workflow.id)"
        >
          <div class="workflow-name">{{ workflow.name }}</div>
          <div class="workflow-meta">创建于 {{ formatDate(workflow.created_at) }}</div>
        </div>
      </div>
      <div class="dialog-actions">
        <Button variant="secondary" @click="showLoadDialog = false">关闭</Button>
      </div>
    </div>
  </div>

  <div v-if="showRunDialog" class="dialog-overlay" @click.self="closeRunDialog">
    <div class="dialog run-dialog">
      <h3>运行工作流</h3>
      <div class="run-meta">
        <span>工作流：</span>
        <strong>{{ currentWorkflowName || currentWorkflowId }}</strong>
      </div>
      <textarea
        v-model="runInput"
        class="run-input"
        placeholder="请输入测试输入"
        :disabled="isRunning"
      ></textarea>
        <div class="run-actions">
        <Button variant="primary" @click="executeWorkflow" :disabled="isRunning">
          运行
        </Button>
        <Button variant="secondary" @click="closeRunDialog" :disabled="isRunning">
          关闭
        </Button>
      </div>
      <div class="run-output">
        <div class="run-section-title">输出</div>
        <pre>{{ runOutput }}</pre>
      </div>
      <div class="run-logs" v-if="runLogs.length">
        <div class="run-section-title">事件</div>
        <ul>
          <li v-for="(log, index) in runLogs" :key="index">{{ log }}</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- 节点配置面板 -->
  <NodeConfigPanel
    :visible="configPanelVisible"
    :node-id="selectedNodeId"
    :node-type="selectedNodeType"
    :node-data="selectedNodeData"
    @close="closeConfigPanel"
    @save="saveNodeConfig"
    @delete="deleteNode"
  />
</div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { VueFlow, useVueFlow, Handle, Position, type Connection } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import StartNode from '../components/nodes/StartNode.vue'
import LLMNode from '../components/nodes/LLMNode.vue'
import KnowledgeNode from '../components/nodes/KnowledgeNode.vue'
import EndNode from '../components/nodes/EndNode.vue'
import ConditionNode from '../components/nodes/ConditionNode.vue'
import NodeConfigPanel from '../components/NodeConfigPanel.vue'
import Button from '@/components/ui/Button.vue'
import axios from 'axios'

import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'

const { addNodes, addEdges, project, toObject, setNodes, setEdges, getNodes, getEdges, updateNode, removeNodes, removeEdges, fitView } = useVueFlow()

const API_BASE = '/api/v1'
const isSaving = ref(false)
const showLoadDialog = ref(false)
interface WorkflowItem {
  id: string
  name: string
  created_at: string
}
const workflows = ref<WorkflowItem[]>([])
const panelAddCount = ref(0)
const drawerOpen = ref(true) // 默认展开
const showRunDialog = ref(false)
const runInput = ref('')
const runOutput = ref('')
const runLogs = ref<string[]>([])
const isRunning = ref(false)
const currentWorkflowId = ref<string | null>(null)
const currentWorkflowName = ref('')

// 配置面板状态
const configPanelVisible = ref(false)
const selectedNodeId = ref<string | null>(null)

// 计算选中的节点类型
const selectedNodeType = computed(() => {
  if (!selectedNodeId.value) return null
  const nodes = getNodes.value
  const node = nodes.find((n: any) => n.id === selectedNodeId.value)
  return node?.type || null
})

// 计算选中的节点数据
const selectedNodeData = computed(() => {
  if (!selectedNodeId.value) return {}
  const nodes = getNodes.value
  const node = nodes.find((n: any) => n.id === selectedNodeId.value)
  return node?.data || {}
})

// 初始节点
const elements = ref([
  {
    id: '1',
    type: 'start',
    label: '开始',
    position: { x: 100, y: 100 },
  },
])

function onConnect(params: Connection) {
  const edgeIdParts = [params.source, params.target, params.sourceHandle, params.targetHandle]
  const edgeId = `e${edgeIdParts.filter(Boolean).join('-')}`
  addEdges({
    id: edgeId,
    source: params.source,
    target: params.target,
    sourceHandle: params.sourceHandle,
    targetHandle: params.targetHandle,
    type: 'smoothstep',
    animated: true
  })
}

// 显示错误提示
function showError(message: string) {
  alert(message)
}

// 保存工作流
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
      nodes: flowData.nodes.map((n: any) => ({
        id: n.id,
        type: n.type,
        position: n.position,
        label: n.label,
        data: n.data || {}
      })),
      edges: flowData.edges.map((e: any) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle,
        targetHandle: e.targetHandle
      }))
    }

    let response
    if (isUpdate) {
      // 更新已有工作流
      response = await axios.put(`${API_BASE}/workflows/${currentWorkflowId.value}`, {
        name: workflowName,
        description: '',
        graph_data: graphData
      })
      showError('工作流更新成功！')
    } else {
      // 创建新工作流
      response = await axios.post(`${API_BASE}/workflows`, {
        name: workflowName,
        description: '',
        graph_data: graphData
      })
      currentWorkflowId.value = response.data.id
      currentWorkflowName.value = response.data.name
      showError('工作流保存成功！')
    }
    console.log('Saved workflow:', response.data)
  } catch (error) {
    console.error('保存工作流失败:', error)
    showError('保存工作流失败')
  } finally {
    isSaving.value = false
  }
}

// 加载工作流列表
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

// 删除工作流
async function deleteWorkflow() {
  if (!currentWorkflowId.value) {
    showError('请先加载一个工作流')
    return
  }

  if (!confirm(`确定要删除工作流「${currentWorkflowName.value}」吗？此操作不可恢复。`)) {
    return
  }

  try {
    await axios.delete(`${API_BASE}/workflows/${currentWorkflowId.value}`)
    showError('工作流删除成功！')
    // 重置状态
    currentWorkflowId.value = null
    currentWorkflowName.value = ''
    setNodes([{ id: '1', type: 'start', label: '开始', position: { x: 100, y: 100 } }])
    setEdges([])
  } catch (error) {
    console.error('删除工作流失败:', error)
    showError('删除工作流失败')
  }
}

// 加载特定工作流
async function loadWorkflow(workflowId: string) {
  try {
    const response = await axios.get(`${API_BASE}/workflows/${workflowId}`)
    const workflow = response.data
    const graphData = workflow.graph_data

    if (graphData && graphData.nodes) {
      setNodes(graphData.nodes.map((n: any) => ({
        id: n.id,
        type: n.type,
        position: n.position,
        label: n.label || getDefaultLabel(n.type),
        data: n.data || {}
      })))
    }

    if (graphData && graphData.edges) {
      setEdges(graphData.edges.map((e: any) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle,
        targetHandle: e.targetHandle
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

function getDefaultLabel(type: string): string {
  const labels: Record<string, string> = {
    start: '开始',
    llm: 'LLM',
    knowledge: '知识库',
    end: '结束',
    condition: '条件'
  }
  return labels[type] || type
}

// 格式化日期
function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
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

function appendRunLog(message: string) {
  runLogs.value.push(message)
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
  isRunning.value = true

  try {
    const response = await fetch(`${API_BASE}/workflows/${currentWorkflowId.value}/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input: runInput.value })
    })

    if (!response.ok || !response.body) {
      throw new Error('执行失败，请检查后端日志')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let currentEvent = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('event: ')) {
          currentEvent = line.slice(7).trim()
        } else if (line.startsWith('data: ')) {
          const dataStr = line.slice(6)
          if (dataStr === '[DONE]') {
            break
          }
          try {
            const data = JSON.parse(dataStr)
            if (currentEvent === 'token') {
              runOutput.value += data.content || ''
            } else if (currentEvent === 'workflow_start') {
              appendRunLog(`开始工作流: ${data.workflow_name || ''}`)
            } else if (currentEvent === 'node_start') {
              appendRunLog(`执行节点: ${data.node_type || ''}`)
            } else if (currentEvent === 'node_complete') {
              appendRunLog(`节点完成: ${data.node_id || ''}`)
            } else if (currentEvent === 'thought') {
              appendRunLog(data.content || data.status || '处理中')
            } else if (currentEvent === 'workflow_complete') {
              appendRunLog('工作流执行完成')
              if (data.final_output) {
                runOutput.value = String(data.final_output)
              }
            } else if (currentEvent === 'workflow_error' || currentEvent === 'node_error') {
              appendRunLog(`错误: ${data.error || '未知错误'}`)
            } else if (currentEvent === 'done') {
              appendRunLog(`状态: ${data.status || 'complete'}`)
            }
          } catch (error) {
            console.warn('解析执行事件失败', error)
          }
        }
      }
    }
  } catch (error) {
    console.error('执行工作流失败:', error)
    showError('执行工作流失败')
  } finally {
    isRunning.value = false
  }
}

// 拖拽开始
function onDragStart(event: DragEvent, nodeType: string) {
  if (event.dataTransfer) {
    event.dataTransfer.setData('application/vueflow', nodeType)
    event.dataTransfer.effectAllowed = 'move'
  }
}

// 拖拽悬停
function onDragOver(event: DragEvent) {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }
}

// 放置节点
function onDrop(event: DragEvent) {
  event.preventDefault()

  const type = event.dataTransfer?.getData('application/vueflow')
  if (!type) return

  const { left, top } = (event.currentTarget as HTMLElement).getBoundingClientRect()
  const position = project({
    x: event.clientX - left,
    y: event.clientY - top,
  })

  const labelMap: Record<string, string> = {
    start: '开始',
    llm: 'LLM',
    knowledge: '知识库',
    end: '结束',
    condition: '条件'
  }

  const newNode = {
    id: `${Date.now()}`,
    type,
    position,
    label: labelMap[type] || type,
    data: {},
  }

  addNodes([newNode])
}

function addNodeFromPanel(type: string) {
  const labelMap: Record<string, string> = {
    start: '开始',
    llm: 'LLM',
    knowledge: '知识库',
    end: '结束',
    condition: '条件'
  }

  const offset = panelAddCount.value * 40
  panelAddCount.value += 1

  const newNode = {
    id: `${Date.now()}-${panelAddCount.value}`,
    type,
    position: { x: 260 + offset, y: 120 + offset },
    label: labelMap[type] || type,
    data: {},
  }

  addNodes([newNode])
}

// 节点点击事件
function onNodeClick(event: any) {
  selectedNodeId.value = event.node.id
  configPanelVisible.value = true
}

// 边点击事件 - 删除边
function onEdgeClick(event: any) {
  const edgeId = event.edge.id
  if (confirm('确定要删除这条连线吗？')) {
    removeEdges([edgeId])
  }
}

// 删除节点
function deleteNode(nodeId: string) {
  if (confirm('确定要删除此节点吗？')) {
    removeNodes([nodeId])
    closeConfigPanel()
  }
}

// 关闭配置面板
function closeConfigPanel() {
  configPanelVisible.value = false
  selectedNodeId.value = null
}

// 保存节点配置
function saveNodeConfig(nodeId: string, data: Record<string, any>) {
  console.log('saveNodeConfig 被调用', nodeId, data)
  const nodes = getNodes.value
  const node = nodes.find((n: any) => n.id === nodeId)
  if (node) {
    console.log('找到节点，更新数据', node)
    // 使用 updateNode 方法更新节点数据，触发响应式更新
    updateNode(nodeId, { data: { ...node.data, ...data } })
    console.log('节点数据已更新')
  } else {
    console.warn('未找到节点', nodeId)
  }
}

// 自动布局
function autoLayout() {
  const nodes = getNodes.value
  const xPositions: Record<string, number> = {
    start: 100,
    llm: 350,
    knowledge: 600,
    condition: 850,
    end: 1100
  }

  // 按类型分组并记录每个类型的当前索引
  const typeIndices: Record<string, number> = {}

  // 创建新的节点数组，更新位置
  const updatedNodes = nodes.map((node: any) => {
    const type = node.type || 'default'
    if (!typeIndices[type]) typeIndices[type] = 0

    const x = xPositions[type] || 100
    const y = 100 + typeIndices[type] * 120
    typeIndices[type]++

    return {
      ...node,
      position: { x, y }
    }
  })

  // 使用 setNodes 批量更新
  setNodes(updatedNodes)

  // 适应视图
  setTimeout(() => {
    fitView()
  }, 100)
}
</script>

<style scoped>
.workflow-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
}

.workflow-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: var(--bg-secondary, #f9fafb);
  border-bottom: 1px solid var(--border-primary, #e5e7eb);
}

.toolbar-left h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary, #111827);
}

.toolbar-right {
  display: flex;
  gap: 8px;
}

.editor-main {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.canvas-container {
  width: 100%;
  flex: 1;
  position: relative;
  background: #f3f4f6;
}

  /* Drawer toggle button */
.drawer-toggle {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 48px;
  background: var(--bg-secondary, #f9fafb);
  border: 1px solid var(--border-primary, #e5e7eb);
  border-right: none;
  border-radius: 4px 0 0 4px;
  cursor: pointer;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: right 0.3s ease;
}

.drawer-toggle.drawer-open {
  right: 220px;
}

.toggle-icon {
  font-size: 12px;
  color: var(--text-secondary, #6b7280);
}

/* Node creation drawer */
.node-drawer {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 220px;
  background: var(--bg-secondary, #f9fafb);
  border-left: 1px solid var(--border-primary, #e5e7eb);
  transform: translateX(100%);
  transition: transform 0.3s ease;
  z-index: 9;
  display: flex;
  flex-direction: column;
}

.node-drawer.open {
  transform: translateX(0);
}

.drawer-title {
  margin: 0;
  padding: 16px;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 1px solid var(--border-primary, #e5e7eb);
}

.drawer-content {
  padding: 12px;
  overflow-y: auto;
  flex: 1;
}

.drawer-node-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  margin-bottom: 8px;
  background: white;
  border: 1px solid var(--border-primary, #e5e7eb);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.drawer-node-item:hover {
  background: var(--bg-primary, #f3f4f6);
  border-color: var(--accent-primary, #3b82f6);
}

.drawer-node-icon {
  font-size: 18px;
}

.drawer-node-label {
  font-size: 14px;
  color: var(--text-primary, #111827);
}

:deep(.vue-flow__node) {
  border: none;
  background: transparent;
  padding: 0;
}

:deep(.vue-flow__handle) {
  width: 8px;
  height: 8px;
  background: #6b7280;
  border: 2px solid white;
}

:deep(.vue-flow__handle:hover) {
  background: #3b82f6;
}

/* Dialog styles */
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

.run-dialog {
  width: 640px;
}

.run-meta {
  font-size: 13px;
  color: #4b5563;
  margin-bottom: 8px;
}

.run-input {
  width: 100%;
  min-height: 90px;
  padding: 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  resize: vertical;
  font-size: 13px;
  margin-bottom: 12px;
}

.run-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.run-output,
.run-logs {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 10px;
  margin-bottom: 10px;
}

.run-output pre {
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  font-size: 12px;
  color: #111827;
}

.run-logs ul {
  padding-left: 18px;
  margin: 6px 0 0;
  font-size: 12px;
  color: #374151;
}

.run-section-title {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.dialog h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: var(--text-primary);
}

.empty-dialog {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-muted);
}

.workflow-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.workflow-item {
  padding: 12px;
  border: 1px solid var(--border-primary);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.workflow-item:hover {
  background-color: var(--bg-secondary);
  border-color: var(--accent-cyan);
}

.workflow-name {
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.workflow-meta {
  font-size: 12px;
  color: var(--text-muted);
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.btn-secondary {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
  border: 1px solid var(--border-primary);
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background-color: var(--bg-secondary);
}
</style>
