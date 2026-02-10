import { ref } from 'vue'

const LABEL_MAP: Record<string, string> = {
  start: '开始',
  llm: 'LLM',
  knowledge: '知识库',
  end: '结束',
  condition: '条件',
  skill: '技能',
}

interface NodePosition {
  x: number
  y: number
}

interface NewNode {
  id: string
  type: string
  position: NodePosition
  label: string
  data: Record<string, unknown>
}

export function useNodeDragDrop(
  addNodes: (nodes: NewNode[]) => void,
  project: (pos: { x: number; y: number }) => NodePosition,
) {
  const panelAddCount = ref(0)

  function onDragStart(event: DragEvent, nodeType: string) {
    if (event.dataTransfer) {
      event.dataTransfer.setData('application/vueflow', nodeType)
      event.dataTransfer.effectAllowed = 'move'
    }
  }

  function onDragOver(event: DragEvent) {
    event.preventDefault()
    if (event.dataTransfer) {
      event.dataTransfer.dropEffect = 'move'
    }
  }

  function onDrop(event: DragEvent) {
    event.preventDefault()
    const type = event.dataTransfer?.getData('application/vueflow')
    if (!type) return

    const { left, top } = (event.currentTarget as HTMLElement).getBoundingClientRect()
    const position = project({ x: event.clientX - left, y: event.clientY - top })

    addNodes([{
      id: crypto.randomUUID(),
      type,
      position,
      label: LABEL_MAP[type] || type,
      data: {},
    }])
  }

  function addNodeFromPanel(type: string) {
    const offset = panelAddCount.value * 40
    panelAddCount.value += 1

    addNodes([{
      id: crypto.randomUUID(),
      type,
      position: { x: 260 + offset, y: 120 + offset },
      label: LABEL_MAP[type] || type,
      data: {},
    }])
  }

  return { panelAddCount, onDragStart, onDragOver, onDrop, addNodeFromPanel }
}
