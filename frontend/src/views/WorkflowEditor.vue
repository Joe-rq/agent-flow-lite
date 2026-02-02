<template>
  <div class="workflow-editor">
    <!-- 左侧节点面板 -->
    <div class="node-panel">
      <div class="panel-header">
        <h3>节点面板</h3>
      </div>
      <div class="panel-actions">
        <button class="btn-save" @click="saveWorkflow" :disabled="isSaving">
          {{ isSaving ? '保存中...' : '保存工作流' }}
        </button>
        <button class="btn-load" @click="showLoadDialog = true">
          加载工作流
        </button>
      </div>
      <div class="panel-content">
        <div
          class="node-item"
          draggable="true"
          @dragstart="onDragStart($event, 'start')"
          @click="addNodeFromPanel('start')"
        >
          <span class="node-item-icon">▶</span>
          <span class="node-item-label">开始节点</span>
        </div>
        <div
          class="node-item"
          draggable="true"
          @dragstart="onDragStart($event, 'llm')"
          @click="addNodeFromPanel('llm')"
        >
          <span class="node-item-icon">🤖</span>
          <span class="node-item-label">LLM 节点</span>
        </div>
        <div
          class="node-item"
          draggable="true"
          @dragstart="onDragStart($event, 'knowledge')"
          @click="addNodeFromPanel('knowledge')"
        >
          <span class="node-item-icon">📚</span>
          <span class="node-item-label">知识库节点</span>
        </div>
        <div
          class="node-item"
          draggable="true"
          @dragstart="onDragStart($event, 'condition')"
          @click="addNodeFromPanel('condition')"
        >
          <span class="node-item-icon">⚡</span>
          <span class="node-item-label">条件节点</span>
        </div>
        <div
          class="node-item"
          draggable="true"
          @dragstart="onDragStart($event, 'end')"
          @click="addNodeFromPanel('end')"
        >
          <span class="node-item-icon">⏹</span>
          <span class="node-item-label">结束节点</span>
        </div>
      </div>
    </div>

    <!-- Vue Flow 画布 -->
    <div class="canvas-container">
      <VueFlow
        v-model="elements"
        :default-zoom="1"
        :min-zoom="0.2"
        :max-zoom="4"
        :default-edge-options="{ type: 'smoothstep', animated: true }"
        @dragover="onDragOver"
        @drop="onDrop"
        @node-click="onNodeClick"
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
          <button class="btn-secondary" @click="showLoadDialog = false">关闭</button>
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
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { VueFlow, useVueFlow, Handle, Position } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import StartNode from '../components/nodes/StartNode.vue'
import LLMNode from '../components/nodes/LLMNode.vue'
import KnowledgeNode from '../components/nodes/KnowledgeNode.vue'
import EndNode from '../components/nodes/EndNode.vue'
import ConditionNode from '../components/nodes/ConditionNode.vue'
import NodeConfigPanel from '../components/NodeConfigPanel.vue'
import axios from 'axios'

import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'

const { addNodes, addEdges, project, toObject, setNodes, setEdges, getNodes, getEdges } = useVueFlow()

const API_BASE = '/api/v1'
const isSaving = ref(false)
const showLoadDialog = ref(false)
const workflows = ref<{ id: string; name: string; created_at: string }[]>([])
const panelAddCount = ref(0)

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

// 显示错误提示
function showError(message: string) {
  alert(message)
}

// 保存工作流
async function saveWorkflow() {
  if (isSaving.value) return
  
  const workflowName = prompt('请输入工作流名称:', '新建工作流')
  if (!workflowName) return
  
  isSaving.value = true
  try {
    const flowData = toObject()
    const response = await axios.post(`${API_BASE}/workflows`, {
      name: workflowName,
      description: '',
      graph_data: {
        nodes: flowData.nodes.map((n: any) => ({
          id: n.id,
          type: n.type,
          position: n.position,
          label: n.label
        })),
        edges: flowData.edges.map((e: any) => ({
          id: e.id,
          source: e.source,
          target: e.target
        }))
      }
    })
    showError('工作流保存成功！')
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
        label: n.label || (n.type === 'start' ? '开始' : n.type === 'llm' ? 'LLM' : '知识库'),
        data: n.data || {}
      })))
    }

    if (graphData && graphData.edges) {
      setEdges(graphData.edges.map((e: any) => ({
        id: e.id,
        source: e.source,
        target: e.target
      })))
    }

    showLoadDialog.value = false
    showError('工作流加载成功！')
  } catch (error) {
    console.error('加载工作流失败:', error)
    showError('加载工作流失败')
  }
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

// 关闭配置面板
function closeConfigPanel() {
  configPanelVisible.value = false
  selectedNodeId.value = null
}

// 保存节点配置
function saveNodeConfig(nodeId: string, data: Record<string, any>) {
  const nodes = getNodes.value
  const node = nodes.find((n: any) => n.id === nodeId)
  if (node) {
    node.data = { ...node.data, ...data }
  }
}
</script>

<style scoped>
.workflow-editor {
  display: flex;
  height: 100%;
  width: 100%;
}

.node-panel {
  width: 25%;
  min-width: 200px;
  max-width: 300px;
  background: #f9fafb;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid #e5e7eb;
  background: white;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.panel-actions {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.btn-save, .btn-load {
  width: 100%;
  padding: 10px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-save {
  background-color: #2c3e50;
  color: white;
}

.btn-save:hover:not(:disabled) {
  background-color: #34495e;
}

.btn-save:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

.btn-load {
  background-color: #ecf0f1;
  color: #2c3e50;
  border: 1px solid #bdc3c7;
}

.btn-load:hover {
  background-color: #d5dbdb;
}

.panel-content {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}

.node-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: grab;
  transition: all 0.2s;
}

.node-item:hover {
  border-color: #3b82f6;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.node-item:active {
  cursor: grabbing;
}

.node-item-icon {
  font-size: 18px;
}

.node-item-label {
  font-size: 14px;
  color: #374151;
  font-weight: 500;
}

.canvas-container {
  width: 75%;
  flex: 1;
  position: relative;
  background: #f3f4f6;
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

.dialog h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: #2c3e50;
}

.empty-dialog {
  text-align: center;
  padding: 40px 20px;
  color: #7f8c8d;
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
  border: 1px solid #e9ecef;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.workflow-item:hover {
  background-color: #f8f9fa;
  border-color: #3498db;
}

.workflow-name {
  font-weight: 500;
  color: #2c3e50;
  margin-bottom: 4px;
}

.workflow-meta {
  font-size: 12px;
  color: #7f8c8d;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
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
</style>
