<template>
  <div class="workflow-view">
    <div class="workflow-toolbar">
      <div class="toolbar-left">
        <h2>工作流编辑器</h2>
      </div>
      <div class="toolbar-right">
        <Button variant="secondary" size="sm" @click="addStartNode">+ 开始节点</Button>
        <Button variant="primary" size="sm" @click="addLLMNode">+ LLM 节点</Button>
        <Button variant="secondary" size="sm" @click="addKnowledgeNode">+ 知识库节点</Button>
        <Button variant="primary" size="sm" @click="saveWorkflow">💾 保存</Button>
      </div>
    </div>

    <div class="workflow-canvas-container">
      <VueFlow
        v-model="elements"
        :default-zoom="1"
        :min-zoom="0.2"
        :max-zoom="4"
        fit-view-on-init
        @node-click="onNodeClick"
        class="light-flow"
      >
        <Background color="#e2e8f0" :gap="20" />
        <Controls />

        <template #node-start="nodeProps">
          <StartNode v-bind="nodeProps" />
        </template>
        <template #node-llm="nodeProps">
          <LLMNode v-bind="nodeProps" />
        </template>
        <template #node-knowledge="nodeProps">
          <KnowledgeNode v-bind="nodeProps" />
        </template>
      </VueFlow>
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
import { ref, computed } from 'vue'
import { VueFlow, useVueFlow, type Node, type Edge } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import axios from 'axios'

import StartNode from '../components/nodes/StartNode.vue'
import LLMNode from '../components/nodes/LLMNode.vue'
import KnowledgeNode from '../components/nodes/KnowledgeNode.vue'
import NodeConfigPanel from '../components/NodeConfigPanel.vue'

import Button from '@/components/ui/Button.vue'

import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'

// Vue Flow 实例
const { addNodes, updateNode, getNodes, getEdges } = useVueFlow()

// 画布元素
const elements = ref<(Node | Edge)[]>([
  {
    id: 'start-1',
    type: 'start',
    label: '开始',
    position: { x: 250, y: 50 },
    data: { inputVariable: '' }
  }
])

// 配置面板状态
const configPanelVisible = ref(false)
const selectedNodeId = ref<string | null>(null)

// 计算选中的节点类型
const selectedNodeType = computed(() => {
  if (!selectedNodeId.value) return null
  const node = elements.value.find(
    (el): el is Node => 'position' in el && el.id === selectedNodeId.value
  )
  return node?.type || null
})

// 计算选中的节点数据
const selectedNodeData = computed(() => {
  if (!selectedNodeId.value) return {}
  const node = elements.value.find(
    (el): el is Node => 'position' in el && el.id === selectedNodeId.value
  )
  return node?.data || {}
})

// 节点 ID 计数器
let nodeIdCounter = 1

// 添加开始节点
const addStartNode = () => {
  nodeIdCounter++
  const newNode: Node = {
    id: `start-${nodeIdCounter}`,
    type: 'start',
    label: '开始',
    position: { x: 250, y: 50 + nodeIdCounter * 100 },
    data: { inputVariable: '' }
  }
  elements.value.push(newNode)
}

// 添加 LLM 节点
const addLLMNode = () => {
  nodeIdCounter++
  const newNode: Node = {
    id: `llm-${nodeIdCounter}`,
    type: 'llm',
    label: 'LLM',
    position: { x: 250, y: 50 + nodeIdCounter * 100 },
    data: {
      systemPrompt: '',
      temperature: 0.7
    }
  }
  elements.value.push(newNode)
}

// 添加知识库节点
const addKnowledgeNode = () => {
  nodeIdCounter++
  const newNode: Node = {
    id: `knowledge-${nodeIdCounter}`,
    type: 'knowledge',
    label: '知识库',
    position: { x: 250, y: 50 + nodeIdCounter * 100 },
    data: { knowledgeBaseId: '' }
  }
  elements.value.push(newNode)
}

// 节点点击事件
const onNodeClick = (event: any) => {
  selectedNodeId.value = event.node.id
  configPanelVisible.value = true
}

// 关闭配置面板
const closeConfigPanel = () => {
  configPanelVisible.value = false
  selectedNodeId.value = null
}

// 保存节点配置
const saveNodeConfig = (nodeId: string, data: Record<string, any>) => {
  const nodeIndex = elements.value.findIndex(
    (el): el is Node => 'position' in el && el.id === nodeId
  )
  if (nodeIndex !== -1) {
    const node = elements.value[nodeIndex] as Node
    node.data = { ...node.data, ...data }
    // 触发更新
    elements.value = [...elements.value]
  }
}

// 保存工作流
const saveWorkflow = async () => {
  try {
    const nodes = getNodes.value.map(node => ({
      id: node.id,
      type: node.type,
      position: node.position,
      data: node.data
    }))

    const edges = getEdges.value.map(edge => ({
      id: edge.id,
      source: edge.source,
      target: edge.target
    }))

    const workflowData = {
      name: '未命名工作流',
      description: '',
      nodes,
      edges
    }

    // 调用后端 API 保存工作流
    const response = await axios.post('/api/v1/workflows/', workflowData)
    
    if (response.status === 200 || response.status === 201) {
      alert('工作流保存成功！')
    } else {
      alert('工作流保存失败，请重试。')
    }
  } catch (error) {
    console.error('保存工作流失败:', error)
    alert('保存工作流失败，请检查网络连接。')
  }
}
</script>

<style scoped>
.workflow-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-primary);
}

.workflow-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-primary);
}

.toolbar-left h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.toolbar-right {
  display: flex;
  gap: 10px;
}

.workflow-canvas-container {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: var(--bg-primary);
}

.dark-flow {
  background: var(--bg-primary);
}

.dark-flow :deep(.vue-flow__node) {
  background: var(--bg-secondary);
  border-color: var(--border-primary);
}

.dark-flow :deep(.vue-flow__handle) {
  background: var(--bg-tertiary);
  border-color: var(--border-primary);
}

.dark-flow :deep(.vue-flow__controls) {
  background: var(--bg-secondary);
  border-color: var(--border-primary);
}

.dark-flow :deep(.vue-flow__controls-button) {
  background: var(--bg-secondary);
  border-color: var(--border-primary);
  color: var(--text-primary);
}

.dark-flow :deep(.vue-flow__controls-button:hover) {
  background: var(--bg-tertiary);
}
</style>
