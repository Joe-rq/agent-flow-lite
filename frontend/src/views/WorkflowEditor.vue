<template>
  <div class="workflow-editor">
    <div class="workflow-toolbar">
      <div class="toolbar-left">
        <h2>工作流编辑器</h2>
      </div>
      <div class="toolbar-right">
        <Button variant="default" size="sm" @click="saveWorkflow" :disabled="isSaving">
          {{ isSaving ? '保存中...' : '保存工作流' }}
        </Button>
        <Button variant="outline" size="sm" @click="loadWorkflows">加载工作流</Button>
        <Button variant="default" size="sm" @click="openRunDialog" :disabled="isRunning">
          {{ isRunning ? '运行中...' : '运行工作流' }}
        </Button>
        <Button variant="destructive" size="sm" @click="deleteWorkflow" :disabled="!currentWorkflowId">
          删除工作流
        </Button>
        <Button variant="outline" size="sm" @click="openExportDialog" :disabled="!currentWorkflowId">
          导出 JSON
        </Button>
        <Button variant="outline" size="sm" @click="openImportDialog">
          导入 JSON
        </Button>
        <Button variant="outline" size="sm" @click="autoLayout">⚡ 自动布局</Button>
      </div>
    </div>

    <div class="editor-main">
      <div class="canvas-container">
      <VueFlow
        v-model="elements"
        :default-zoom="1" :min-zoom="0.2" :max-zoom="4"
        :default-edge-options="{ type: 'smoothstep', animated: true }"
        :delete-key-code="'Delete'" :snap-to-grid="true" :snap-grid="[20, 20]"
        @dragover="onDragOver" @drop="onDrop"
        @node-click="onNodeClick" @edge-click="onEdgeClick"
        @connect="onConnect" fit-view-on-init
      >
        <Background pattern-color="#e5e7eb" :gap="20" />
        <Controls />
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
        <template #node-skill="props">
          <SkillNode v-bind="props" />
          <Handle type="target" :position="Position.Left" />
          <Handle type="source" :position="Position.Right" />
        </template>
        <template #node-http="props">
          <HttpNode v-bind="props" />
          <Handle type="target" :position="Position.Left" />
          <Handle type="source" :position="Position.Right" />
        </template>
        <template #node-code="props">
          <CodeNode v-bind="props" />
          <Handle type="target" :position="Position.Left" />
          <Handle type="source" :position="Position.Right" />
        </template>
      </VueFlow>
      <NodeDrawer
        :show-drawer="drawerOpen" :enabled-node-types="enabledNodeTypes" @toggle="drawerOpen = !drawerOpen"
        @add-node="addNodeFromPanel" @drag-start="onDragStart"
      />
    </div>
  </div>

  <WorkflowLoadDialog
    :show-load-dialog="showLoadDialog" :workflows="workflows"
    @load="loadWorkflow" @close="showLoadDialog = false"
  />
  <WorkflowRunDialog
    :show-run-dialog="showRunDialog" :is-running="isRunning"
    :run-input="runInput" :run-output="runOutput" :run-logs="runLogs"
    :workflow-name="currentWorkflowName || currentWorkflowId || ''"
    @update:run-input="runInput = $event"
    @execute="executeWorkflow" @close="closeRunDialog"
  />
  <WorkflowImportExportDialog
    :visible="showImportExportDialog"
    :mode="importExportMode"
    :export-data="exportData"
    :is-exporting="isExporting"
    :export-error="exportError"
    :is-importing="isImporting"
    :import-error="importError"
    @close="closeImportExportDialog"
    @import="importWorkflow"
    @import-template="importWorkflow"
  />
  <NodeConfigPanel
    :visible="configPanelVisible" :node-id="selectedNodeId"
    :node-type="selectedNodeType" :node-data="selectedNodeData"
    @close="closeConfigPanel" @save="saveNodeConfig" @delete="deleteNode"
  />
</div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { VueFlow, useVueFlow, Handle, Position } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import StartNode from '../components/nodes/StartNode.vue'
import LLMNode from '../components/nodes/LLMNode.vue'
import KnowledgeNode from '../components/nodes/KnowledgeNode.vue'
import EndNode from '../components/nodes/EndNode.vue'
import ConditionNode from '../components/nodes/ConditionNode.vue'
import HttpNode from '../components/nodes/HttpNode.vue'
import CodeNode from '../components/nodes/CodeNode.vue'
import SkillNode from '../components/nodes/SkillNode.vue'
import NodeConfigPanel from '../components/NodeConfigPanel.vue'
import Button from '@/components/ui/Button.vue'
import NodeDrawer from '@/components/workflow/NodeDrawer.vue'
import WorkflowLoadDialog from '@/components/workflow/WorkflowLoadDialog.vue'
import WorkflowRunDialog from '@/components/workflow/WorkflowRunDialog.vue'
import WorkflowImportExportDialog from '@/components/workflow/WorkflowImportExportDialog.vue'
import { useWorkflowCrud } from '@/composables/workflow/useWorkflowCrud'
import { useWorkflowExecution } from '@/composables/workflow/useWorkflowExecution'
import { useNodeDragDrop } from '@/composables/workflow/useNodeDragDrop'
import { useEditorActions } from '@/composables/workflow/useEditorActions'
import { useFeatureFlags } from '@/composables/workflow/useFeatureFlags'

import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'

const flow = useVueFlow()
const { addNodes, project, toObject, setNodes, setEdges } = flow

const {
  isSaving, showLoadDialog, workflows, currentWorkflowId, currentWorkflowName,
  saveWorkflow, loadWorkflows, deleteWorkflow, loadWorkflow,
  showImportExportDialog, importExportMode, exportData,
  isExporting, exportError, isImporting, importError,
  openExportDialog, openImportDialog, closeImportExportDialog,
  importWorkflow,
} = useWorkflowCrud(toObject, setNodes, setEdges)

const {
  isRunning, runInput, runOutput, runLogs, showRunDialog,
  openRunDialog, closeRunDialog, executeWorkflow,
} = useWorkflowExecution(currentWorkflowId)

const { onDragStart, onDragOver, onDrop, addNodeFromPanel } = useNodeDragDrop(addNodes, project)

const {
  configPanelVisible, selectedNodeId, selectedNodeType, selectedNodeData,
  onConnect, onNodeClick, onEdgeClick, deleteNode, closeConfigPanel,
  saveNodeConfig, autoLayout,
} = useEditorActions(flow)

const drawerOpen = ref(true)
const { enabledNodeTypes, loadFeatureFlags } = useFeatureFlags()

const elements = ref([
  { id: '1', type: 'start', label: '开始', position: { x: 100, y: 100 } },
])

onMounted(() => {
  loadFeatureFlags()
})
</script>

<style scoped src="./WorkflowEditor.css"></style>
