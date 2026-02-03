import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia } from 'pinia'
import HomeView from '@/views/HomeView.vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'

// 创建测试用的 router
function createTestRouter() {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/', component: HomeView },
      { path: '/workflow', component: { template: '<div>Workflow</div>' } },
      { path: '/knowledge', component: { template: '<div>Knowledge</div>' } },
      { path: '/chat', component: { template: '<div>Chat</div>' } }
    ]
  })
}

describe('HomeView Smoke Tests', () => {
  let router: ReturnType<typeof createTestRouter>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(async () => {
    router = createTestRouter()
    pinia = createPinia()
    await router.push('/')
    await router.isReady()
  })

  it('should mount component successfully', () => {
    const wrapper = mount(HomeView, {
      global: {
        plugins: [router, pinia],
        components: {
          Card,
          Button
        }
      }
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('should display Chinese title', () => {
    const wrapper = mount(HomeView, {
      global: {
        plugins: [router, pinia],
        components: {
          Card,
          Button
        }
      }
    })
    expect(wrapper.text()).toContain('构建、管理和部署智能 AI 工作流')
  })

  it('should display feature cards in Chinese', () => {
    const wrapper = mount(HomeView, {
      global: {
        plugins: [router, pinia],
        components: {
          Card,
          Button
        }
      }
    })
    const text = wrapper.text()
    expect(text).toContain('工作流')
    expect(text).toContain('知识库')
    expect(text).toContain('对话')
  })

  it('should display CTA buttons in Chinese', () => {
    const wrapper = mount(HomeView, {
      global: {
        plugins: [router, pinia],
        components: {
          Card,
          Button
        }
      }
    })
    const text = wrapper.text()
    expect(text).toContain('创建工作流')
    expect(text).toContain('上传文档')
  })

  it('should render three feature cards', () => {
    const wrapper = mount(HomeView, {
      global: {
        plugins: [router, pinia],
        components: {
          Card,
          Button
        }
      }
    })
    const cards = wrapper.findAllComponents(Card)
    expect(cards.length).toBe(3)
  })
})
