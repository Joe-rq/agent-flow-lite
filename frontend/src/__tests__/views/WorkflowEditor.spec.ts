import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia } from 'pinia'
import WorkflowEditor from '@/views/WorkflowEditor.vue'

// Mock Vue Flow
vi.mock('@vue-flow/core', () => ({
  VueFlow: {
    name: 'VueFlow',
    template: '<div data-testid="vue-flow"><slot /></div>',
  },
  useVueFlow: () => ({
    addNodes: vi.fn(),
    addEdges: vi.fn(),
    project: vi.fn(),
    toObject: vi.fn(),
    setNodes: vi.fn(),
    setEdges: vi.fn(),
    getNodes: vi.fn(() => []),
    getEdges: vi.fn(() => []),
    updateNode: vi.fn(),
    removeNodes: vi.fn(),
    removeEdges: vi.fn(),
    fitView: vi.fn(),
  }),
  Handle: {
    name: 'Handle',
    template: '<div data-testid="handle" />',
  },
  Position: { Left: 'left', Right: 'right' },
}))

// Mock other components
vi.mock('@vue-flow/background', () => ({
  Background: {
    name: 'Background',
    template: '<div data-testid="background" />',
  },
}))

vi.mock('@vue-flow/controls', () => ({
  Controls: {
    name: 'Controls',
    template: '<div data-testid="controls" />',
  },
}))

vi.mock('@/components/nodes/StartNode.vue', () => ({
  default: { name: 'StartNode', template: '<div>Start</div>' },
}))
vi.mock('@/components/nodes/LLMNode.vue', () => ({
  default: { name: 'LLMNode', template: '<div>LLM</div>' },
}))
vi.mock('@/components/nodes/KnowledgeNode.vue', () => ({
  default: { name: 'KnowledgeNode', template: '<div>Knowledge</div>' },
}))
vi.mock('@/components/nodes/EndNode.vue', () => ({
  default: { name: 'EndNode', template: '<div>End</div>' },
}))
vi.mock('@/components/nodes/ConditionNode.vue', () => ({
  default: { name: 'ConditionNode', template: '<div>Condition</div>' },
}))

vi.mock('@/components/NodeConfigPanel.vue', () => ({
  default: { name: 'NodeConfigPanel', template: '<div data-testid="config-panel" />' },
}))

const router = createRouter({
  history: createWebHistory(),
  routes: [{ path: '/workflow', component: WorkflowEditor }],
})

const pinia = createPinia()

describe('WorkflowEditor Smoke Tests', () => {
  const mountOptions = {
    global: {
      plugins: [router, pinia],
      stubs: {
        Button: { template: '<button><slot /></button>' }
      },
    },
  }

  it('should mount component successfully', async () => {
    const wrapper = mount(WorkflowEditor, mountOptions)
    expect(wrapper.exists()).toBe(true)
  })

  it('should display toolbar buttons in Chinese', async () => {
    const wrapper = mount(WorkflowEditor, mountOptions)
    const text = wrapper.text()
    expect(text).toContain('保存工作流')
    expect(text).toContain('加载工作流')
    expect(text).toContain('运行工作流')
    expect(text).toContain('删除工作流')
    expect(text).toContain('自动布局')
  })

  it('should display left panel with workflow info', async () => {
    const wrapper = mount(WorkflowEditor, mountOptions)
    const text = wrapper.text()
    expect(text).toContain('工作流信息')
    expect(text).toContain('名称')
    expect(text).toContain('ID')
    expect(text).toContain('状态')
  })

  it('should display drawer with node creation buttons', async () => {
    const wrapper = mount(WorkflowEditor, mountOptions)
    const text = wrapper.text()
    expect(text).toContain('添加节点')
    expect(text).toContain('开始节点')
    expect(text).toContain('LLM 节点')
    expect(text).toContain('知识库节点')
    expect(text).toContain('条件节点')
    expect(text).toContain('结束节点')
  })
})
