import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia } from 'pinia'
import KnowledgeView from '@/views/KnowledgeView.vue'

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: [] }),
    post: vi.fn().mockResolvedValue({ status: 200 }),
    delete: vi.fn().mockResolvedValue({ status: 200 })
  }
}))

function createTestRouter() {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/knowledge', component: KnowledgeView }
    ]
  })
}

describe('KnowledgeView Smoke Tests', () => {
  let router: ReturnType<typeof createTestRouter>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(async () => {
    router = createTestRouter()
    pinia = createPinia()
    await router.push('/knowledge')
    await router.isReady()
  })

  it('should mount component successfully', () => {
    const wrapper = mount(KnowledgeView, {
      global: {
        plugins: [router, pinia]
      }
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('should display Chinese title', () => {
    const wrapper = mount(KnowledgeView, {
      global: {
        plugins: [router, pinia]
      }
    })
    expect(wrapper.text()).toContain('知识库管理')
  })

  it('should display buttons in Chinese', () => {
    const wrapper = mount(KnowledgeView, {
      global: {
        plugins: [router, pinia]
      }
    })
    const text = wrapper.text()
    expect(text).toContain('新建知识库')
  })

  it('should display empty state in Chinese', () => {
    const wrapper = mount(KnowledgeView, {
      global: {
        plugins: [router, pinia]
      }
    })
    expect(wrapper.text()).toContain('暂无知识库')
  })
})
