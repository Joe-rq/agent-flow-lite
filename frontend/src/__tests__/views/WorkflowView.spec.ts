import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia } from 'pinia'
import WorkflowView from '@/views/WorkflowView.vue'

// Mock Vue Flow components
vi.mock('@vue-flow/core', () => ({
  VueFlow: {
    name: 'VueFlow',
    template: '<div class="vue-flow-mock"><slot /></div>',
    props: ['modelValue', 'defaultZoom', 'minZoom', 'maxZoom']
  },
  useVueFlow: () => ({
    addNodes: vi.fn(),
    updateNode: vi.fn(),
    getNodes: { value: [] },
    getEdges: { value: [] }
  })
}))

vi.mock('@vue-flow/background', () => ({
  Background: {
    name: 'Background',
    template: '<div class="background-mock" />'
  }
}))

vi.mock('@vue-flow/controls', () => ({
  Controls: {
    name: 'Controls',
    template: '<div class="controls-mock" />'
  }
}))

// Mock axios
vi.mock('axios', () => ({
  default: {
    post: vi.fn().mockResolvedValue({ status: 200 })
  }
}))

function createTestRouter() {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/workflow', component: WorkflowView }
    ]
  })
}

describe('WorkflowView Smoke Tests', () => {
  let router: ReturnType<typeof createTestRouter>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(async () => {
    router = createTestRouter()
    pinia = createPinia()
    await router.push('/workflow')
    await router.isReady()
  })

  it('should mount component successfully', () => {
    const wrapper = mount(WorkflowView, {
      global: {
        plugins: [router, pinia]
      }
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('should display Chinese title', () => {
    const wrapper = mount(WorkflowView, {
      global: {
        plugins: [router, pinia]
      }
    })
    expect(wrapper.text()).toContain('工作流编辑器')
  })

  it('should display toolbar buttons in Chinese', () => {
    const wrapper = mount(WorkflowView, {
      global: {
        plugins: [router, pinia]
      }
    })
    const text = wrapper.text()
    expect(text).toContain('开始节点')
    expect(text).toContain('LLM 节点')
    expect(text).toContain('知识库节点')
    expect(text).toContain('保存')
  })
})
