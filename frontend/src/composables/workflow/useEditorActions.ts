import { ref, computed } from 'vue'
import type { Connection } from '@vue-flow/core'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function useEditorActions(flow: any) {
  const configPanelVisible = ref(false)
  const selectedNodeId = ref<string | null>(null)

  const selectedNodeType = computed(() => {
    if (!selectedNodeId.value) return null
    const node = flow.getNodes.value.find((n: { id: string; type?: string }) => n.id === selectedNodeId.value)
    return node?.type || null
  })

  const selectedNodeData = computed(() => {
    if (!selectedNodeId.value) return {}
    const node = flow.getNodes.value.find((n: { id: string; data?: Record<string, unknown> }) => n.id === selectedNodeId.value)
    return node?.data || {}
  })

  function onConnect(params: Connection) {
    const parts = [params.source, params.target, params.sourceHandle, params.targetHandle]
    flow.addEdges({
      id: `e${parts.filter(Boolean).join('-')}`,
      source: params.source, target: params.target,
      sourceHandle: params.sourceHandle, targetHandle: params.targetHandle,
      type: 'smoothstep', animated: true,
    })
  }

  function onNodeClick(event: { node: { id: string } }) {
    selectedNodeId.value = event.node.id
    configPanelVisible.value = true
  }

  function onEdgeClick(event: { edge: { id: string } }) {
    if (confirm('确定要删除这条连线吗？')) flow.removeEdges([event.edge.id])
  }

  function deleteNode(nodeId: string) {
    if (confirm('确定要删除此节点吗？')) {
      flow.removeNodes([nodeId])
      closeConfigPanel()
    }
  }

  function closeConfigPanel() {
    configPanelVisible.value = false
    selectedNodeId.value = null
  }

  function saveNodeConfig(nodeId: string, data: Record<string, unknown>) {
    const node = flow.getNodes.value.find((n: { id: string; data?: Record<string, unknown> }) => n.id === nodeId)
    if (node) flow.updateNode(nodeId, { data: { ...node.data, ...data } })
    else console.warn('未找到节点', nodeId)
  }

  function autoLayout() {
    const xPos: Record<string, number> = {
      start: 100, llm: 350, knowledge: 600, skill: 600, condition: 850, end: 1100,
    }
    const idx: Record<string, number> = {}
    const updated = flow.getNodes.value.map((node: { type?: string; position: { x: number; y: number } }) => {
      const type = node.type || 'default'
      if (!idx[type]) idx[type] = 0
      const x = xPos[type] || 100
      const y = 100 + idx[type] * 120
      idx[type]++
      return { ...node, position: { x, y } }
    })
    flow.setNodes(updated)
    setTimeout(() => flow.fitView(), 100)
  }

  return {
    configPanelVisible, selectedNodeId, selectedNodeType, selectedNodeData,
    onConnect, onNodeClick, onEdgeClick, deleteNode, closeConfigPanel,
    saveNodeConfig, autoLayout,
  }
}
