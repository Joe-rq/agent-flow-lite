<template>
  <div class="workflow-editor">
    <!-- 左侧节点面板 -->
    <div class="node-panel">
      <div class="panel-header">
        <h3>节点面板</h3>
      </div>
      <div class="panel-content">
        <div
          class="node-item"
          draggable="true"
          @dragstart="onDragStart($event, 'start')"
        >
          <span class="node-item-icon">▶</span>
          <span class="node-item-label">开始节点</span>
        </div>
        <div
          class="node-item"
          draggable="true"
          @dragstart="onDragStart($event, 'llm')"
        >
          <span class="node-item-icon">🤖</span>
          <span class="node-item-label">LLM 节点</span>
        </div>
        <div
          class="node-item"
          draggable="true"
          @dragstart="onDragStart($event, 'knowledge')"
        >
          <span class="node-item-icon">📚</span>
          <span class="node-item-label">知识库节点</span>
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
        @dragover="onDragOver"
        @drop="onDrop"
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
      </VueFlow>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { VueFlow, useVueFlow, Handle, Position } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import StartNode from '../components/nodes/StartNode.vue'
import LLMNode from '../components/nodes/LLMNode.vue'
import KnowledgeNode from '../components/nodes/KnowledgeNode.vue'

import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'

const { addNodes, addEdges, project } = useVueFlow()

// 初始节点
const elements = ref([
  {
    id: '1',
    type: 'start',
    label: '开始',
    position: { x: 100, y: 100 },
  },
])

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

  const newNode = {
    id: `${Date.now()}`,
    type,
    position,
    label: type === 'start' ? '开始' : type === 'llm' ? 'LLM' : '知识库',
  }

  addNodes([newNode])
}
</script>

<style scoped>
.workflow-editor {
  display: flex;
  height: 100vh;
  width: 100%;
}

.node-panel {
  width: 240px;
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

.panel-content {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
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
</style>
