import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia } from 'pinia'
import SkillEditor from '@/views/SkillEditor.vue'

const mockGet = vi.fn()
const mockPost = vi.fn()
const mockPut = vi.fn()

vi.mock('axios', () => ({
  default: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
    put: (...args: unknown[]) => mockPut(...args),
  }
}))

function createTestRouter() {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/skills/new', component: SkillEditor },
      { path: '/skills/:name', component: SkillEditor },
      { path: '/skills', component: { template: '<div>Skills List</div>' } }
    ]
  })
}

describe('SkillEditor Smoke Tests', () => {
  let router: ReturnType<typeof createTestRouter>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(async () => {
    router = createTestRouter()
    pinia = createPinia()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('should mount component successfully for new skill', async () => {
    await router.push('/skills/new')
    await router.isReady()

    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('should display new skill title', async () => {
    await router.push('/skills/new')
    await router.isReady()

    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })
    expect(wrapper.text()).toContain('新建技能')
  })

  it('should display edit skill title when editing', async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        name: 'test-skill',
        description: 'Test description',
        model: 'deepseek-chat',
        inputs: [],
        prompt: 'Test prompt',
      }
    })

    await router.push('/skills/test-skill')
    await router.isReady()

    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    await flushPromises()
    expect(wrapper.text()).toContain('编辑技能')
  })

  it('should have form fields', async () => {
    await router.push('/skills/new')
    await router.isReady()

    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })
    const text = wrapper.text()
    expect(text).toContain('技能名称')
    expect(text).toContain('描述')
    expect(text).toContain('输入参数')
    expect(text).toContain('提示词')
  })

  it('should have save button', async () => {
    await router.push('/skills/new')
    await router.isReady()

    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })
    expect(wrapper.text()).toContain('保存')
  })

  it('should have preview toggle', async () => {
    await router.push('/skills/new')
    await router.isReady()

    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })
    expect(wrapper.text()).toContain('隐藏预览')
  })
})

describe('SkillEditor Form Validation', () => {
  let router: ReturnType<typeof createTestRouter>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(async () => {
    router = createTestRouter()
    pinia = createPinia()
    await router.push('/skills/new')
    await router.isReady()
    vi.clearAllMocks()
  })

  it('should validate skill name format', async () => {
    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    const nameInput = wrapper.find('input[type="text"]')
    await nameInput.setValue('Invalid_Name')
    await nameInput.trigger('blur')

    expect(wrapper.text()).toContain('只能包含小写字母、数字、连字符')
  })

  it('should validate name cannot start with hyphen', async () => {
    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    const nameInput = wrapper.find('input[type="text"]')
    await nameInput.setValue('-invalid-name')
    await nameInput.trigger('blur')

    expect(wrapper.text()).toContain('不能以连字符开头或结尾')
  })

  it('should validate name cannot end with hyphen', async () => {
    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    const nameInput = wrapper.find('input[type="text"]')
    await nameInput.setValue('invalid-name-')
    await nameInput.trigger('blur')

    expect(wrapper.text()).toContain('不能以连字符开头或结尾')
  })

  it('should validate name cannot have consecutive hyphens', async () => {
    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    const nameInput = wrapper.find('input[type="text"]')
    await nameInput.setValue('invalid--name')
    await nameInput.trigger('blur')

    expect(wrapper.text()).toContain('不能有连续连字符')
  })

  it('should accept valid skill name', async () => {
    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    const nameInput = wrapper.find('input[type="text"]')
    await nameInput.setValue('valid-skill-name')
    await nameInput.trigger('blur')

    expect(wrapper.text()).not.toContain('只能包含小写字母')
    expect(wrapper.text()).not.toContain('不能以连字符开头')
  })

  it('should not save when name is empty', async () => {
    mockPost.mockResolvedValueOnce({ status: 201 })

    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    const textarea = wrapper.find('.prompt-textarea')
    await textarea.setValue('Test prompt content')

    const saveButton = wrapper.findAll('button').find(b => b.text().includes('保存') && !b.text().includes('隐藏'))
    if (saveButton) {
      await saveButton.trigger('click')
    }

    await flushPromises()

    expect(mockPost).not.toHaveBeenCalled()
  })

  it('should show error when prompt is empty on save', async () => {
    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    const nameInput = wrapper.find('input[type="text"]')
    await nameInput.setValue('test-skill')

    const saveButton = wrapper.findAll('button').find(b => b.text().includes('保存'))
    if (saveButton) {
      await saveButton.trigger('click')
    }

    expect(wrapper.text()).toContain('请输入提示词内容')
  })
})

describe('SkillEditor Input Parameters', () => {
  let router: ReturnType<typeof createTestRouter>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(async () => {
    router = createTestRouter()
    pinia = createPinia()
    await router.push('/skills/new')
    await router.isReady()
    vi.clearAllMocks()
  })

  it('should add input parameter', async () => {
    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    const addButton = wrapper.findAll('button').find(b => b.text().includes('添加'))
    if (addButton) {
      await addButton.trigger('click')
    }

    expect(wrapper.findAll('.input-row').length).toBe(1)
  })

  it('should remove input parameter', async () => {
    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    const addButton = wrapper.findAll('button').find(b => b.text().includes('添加'))
    if (addButton) {
      await addButton.trigger('click')
    }

    expect(wrapper.findAll('.input-row').length).toBe(1)

    const removeButton = wrapper.find('.btn-remove')
    await removeButton.trigger('click')

    expect(wrapper.findAll('.input-row').length).toBe(0)
  })

  it('should show empty state when no inputs', async () => {
    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    expect(wrapper.text()).toContain('暂无输入参数')
  })

  it('should update input values', async () => {
    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    const addButton = wrapper.findAll('button').find(b => b.text().includes('添加'))
    if (addButton) {
      await addButton.trigger('click')
    }

    const inputs = wrapper.findAll('.input-row input')
    await inputs[0].setValue('myParam')
    await inputs[1].setValue('Parameter description')
    await inputs[2].setValue('defaultValue')

    expect(inputs[0].element.value).toBe('myParam')
    expect(inputs[1].element.value).toBe('Parameter description')
    expect(inputs[2].element.value).toBe('defaultValue')
  })

  it('should toggle required checkbox', async () => {
    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    const addButton = wrapper.findAll('button').find(b => b.text().includes('添加'))
    if (addButton) {
      await addButton.trigger('click')
    }

    const checkbox = wrapper.find('.checkbox-label input[type="checkbox"]')
    expect(checkbox.element.checked).toBe(false)

    await checkbox.setValue(true)
    expect(checkbox.element.checked).toBe(true)
  })
})

describe('SkillEditor Variable Detection', () => {
  let router: ReturnType<typeof createTestRouter>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(async () => {
    router = createTestRouter()
    pinia = createPinia()
    await router.push('/skills/new')
    await router.isReady()
    vi.clearAllMocks()
  })

  it('should detect variables in prompt', async () => {
    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    const textarea = wrapper.find('.prompt-textarea')
    await textarea.setValue('Hello {{name}}, your age is {{age}}')

    expect(wrapper.text()).toContain('name')
    expect(wrapper.text()).toContain('age')
  })

  it('should mark declared variables as valid', async () => {
    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    const addButton = wrapper.findAll('button').find(b => b.text().includes('添加'))
    if (addButton) {
      await addButton.trigger('click')
    }

    const inputs = wrapper.findAll('.input-row input')
    await inputs[0].setValue('name')

    const textarea = wrapper.find('.prompt-textarea')
    await textarea.setValue('Hello {{name}}')

    expect(wrapper.find('.variable-tag.declared').exists()).toBe(true)
  })

  it('should mark undeclared variables as warning', async () => {
    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    const textarea = wrapper.find('.prompt-textarea')
    await textarea.setValue('Hello {{undeclared}}')

    const undeclaredTag = wrapper.find('.variable-tag:not(.declared)')
    expect(undeclaredTag.exists()).toBe(true)
    expect(undeclaredTag.text()).toContain('未声明')
  })

  it('should show empty state when no variables', async () => {
    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    expect(wrapper.text()).toContain('未检测到变量')
  })
})

describe('SkillEditor Preview', () => {
  let router: ReturnType<typeof createTestRouter>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(async () => {
    router = createTestRouter()
    pinia = createPinia()
    await router.push('/skills/new')
    await router.isReady()
    vi.clearAllMocks()
  })

  it('should toggle preview visibility', async () => {
    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    expect(wrapper.find('.preview-pane').exists()).toBe(true)

    const toggleButton = wrapper.findAll('button').find(b => b.text().includes('隐藏预览'))
    if (toggleButton) {
      await toggleButton.trigger('click')
    }

    expect(wrapper.find('.preview-pane').exists()).toBe(false)
    expect(wrapper.text()).toContain('显示预览')
  })

  it('should generate correct markdown preview', async () => {
    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    const nameInput = wrapper.find('input[type="text"]')
    await nameInput.setValue('test-skill')

    const textarea = wrapper.find('.prompt-textarea')
    await textarea.setValue('Process this: {{text}}')

    const previewContent = wrapper.find('.code-block').text()
    expect(previewContent).toContain('name: test-skill')
    expect(previewContent).toContain('Process this: {{text}}')
  })

  it('should include description in markdown preview', async () => {
    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    const inputs = wrapper.findAll('.form-group input')
    await inputs[0].setValue('test-skill')
    await inputs[1].setValue('deepseek-chat')

    const descriptionInput = wrapper.findAll('.form-group input')[2] || wrapper.findAll('input')[1]
    if (descriptionInput) {
      await descriptionInput.setValue('A test skill')
    }

    const textarea = wrapper.find('.prompt-textarea')
    await textarea.setValue('Test prompt')

    const previewContent = wrapper.find('.code-block').text()
    expect(previewContent).toContain('A test skill')
  })
})

describe('SkillEditor Save', () => {
  let router: ReturnType<typeof createTestRouter>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(async () => {
    router = createTestRouter()
    pinia = createPinia()
    await router.push('/skills/new')
    await router.isReady()
    vi.resetAllMocks()
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  it('should create new skill successfully', async () => {
    mockPost.mockResolvedValueOnce({ status: 201 })
    const pushSpy = vi.spyOn(router, 'push')

    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    const nameInput = wrapper.find('input[type="text"]')
    await nameInput.setValue('new-skill')

    const textarea = wrapper.find('.prompt-textarea')
    await textarea.setValue('Test prompt content')

    const saveButton = wrapper.findAll('button').find(b => b.text().includes('保存') && !b.text().includes('隐藏'))
    if (saveButton) {
      await saveButton.trigger('click')
    }

    await flushPromises()

    expect(mockPost).toHaveBeenCalledWith(
      '/api/v1/skills',
      expect.objectContaining({
        name: 'new-skill',
        prompt: 'Test prompt content'
      })
    )
    expect(pushSpy).toHaveBeenCalledWith('/skills')
  })

  it('should update existing skill successfully', async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        name: 'existing-skill',
        description: 'Existing description',
        model: 'deepseek-chat',
        inputs: [],
        prompt: 'Existing prompt',
      }
    })
    mockPut.mockResolvedValueOnce({ status: 200 })
    const pushSpy = vi.spyOn(router, 'push')

    await router.push('/skills/existing-skill')
    await router.isReady()

    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    await flushPromises()

    const textarea = wrapper.find('.prompt-textarea')
    await textarea.setValue('Updated prompt content')

    const saveButton = wrapper.findAll('button').find(b => b.text().includes('保存') && !b.text().includes('隐藏'))
    if (saveButton) {
      await saveButton.trigger('click')
    }

    await flushPromises()

    expect(mockPut).toHaveBeenCalledWith(
      '/api/v1/skills/existing-skill',
      expect.objectContaining({
        name: 'existing-skill',
        prompt: 'Updated prompt content'
      })
    )
    expect(pushSpy).toHaveBeenCalledWith('/skills')
  })

  it('should show error when save fails', async () => {
    mockPost.mockRejectedValueOnce({
      response: { data: { detail: 'Skill already exists' } }
    })

    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    const nameInput = wrapper.find('input[type="text"]')
    await nameInput.setValue('existing-skill')

    const textarea = wrapper.find('.prompt-textarea')
    await textarea.setValue('Test prompt')

    const saveButton = wrapper.findAll('button').find(b => b.text().includes('保存') && !b.text().includes('隐藏'))
    if (saveButton) {
      await saveButton.trigger('click')
    }

    await flushPromises()

    expect(wrapper.text()).toContain('Skill already exists')
  })

  it('should disable save button while saving', async () => {
    let resolveSave: (value: unknown) => void
    mockPost.mockImplementationOnce(() => new Promise((resolve) => {
      resolveSave = resolve
    }))

    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    const nameInput = wrapper.find('input[type="text"]')
    await nameInput.setValue('new-skill')

    const textarea = wrapper.find('.prompt-textarea')
    await textarea.setValue('Test prompt')

    await flushPromises()

    const saveButton = wrapper.find('.btn-primary')
    expect(saveButton.exists()).toBe(true)
    await saveButton.trigger('click')

    await flushPromises()

    expect(wrapper.text()).toContain('保存中...')

    resolveSave!({ status: 201 })
  })

  it('should include inputs in save payload', async () => {
    mockPost.mockResolvedValueOnce({ status: 201 })

    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    const nameInput = wrapper.find('input[type="text"]')
    await nameInput.setValue('skill-with-inputs')

    const addButton = wrapper.findAll('button').find(b => b.text().includes('添加'))
    if (addButton) {
      await addButton.trigger('click')
    }

    const inputs = wrapper.findAll('.input-row input')
    await inputs[0].setValue('article')
    await inputs[1].setValue('Article content')

    const checkbox = wrapper.find('.checkbox-label input[type="checkbox"]')
    await checkbox.setValue(true)

    const textarea = wrapper.find('.prompt-textarea')
    await textarea.setValue('Summarize: {{article}}')

    const saveButton = wrapper.findAll('button').find(b => b.text().includes('保存') && !b.text().includes('隐藏'))
    if (saveButton) {
      await saveButton.trigger('click')
    }

    await flushPromises()

    expect(mockPost).toHaveBeenCalledWith(
      '/api/v1/skills',
      expect.objectContaining({
        inputs: expect.arrayContaining([
          expect.objectContaining({
            name: 'article',
            description: 'Article content',
            required: true
          })
        ])
      })
    )
  })

  it('should include content field in create payload', async () => {
    mockPost.mockResolvedValueOnce({ status: 201 })

    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    const nameInput = wrapper.find('input[type="text"]')
    await nameInput.setValue('new-skill')

    const textarea = wrapper.find('.prompt-textarea')
    await textarea.setValue('Test prompt content')

    const saveButton = wrapper.findAll('button').find(b => b.text().includes('保存') && !b.text().includes('隐藏'))
    if (saveButton) {
      await saveButton.trigger('click')
    }

    await flushPromises()

    // Calculate expected content (generatedMarkdown output)
    const expectedContent = `---\nname: new-skill\n---\n\nTest prompt content`

    // Verify POST was called with content field
    expect(mockPost).toHaveBeenCalled()
    const [, createPayload] = mockPost.mock.calls[0]
    expect(createPayload.content).toBe(expectedContent)
  })

  it('should include content field in update payload', async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        name: 'existing-skill',
        description: 'Existing description',
        model: 'deepseek-chat',
        inputs: [],
        prompt: 'Existing prompt',
      }
    })
    mockPut.mockResolvedValueOnce({ status: 200 })

    await router.push('/skills/existing-skill')
    await router.isReady()

    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    await flushPromises()

    const textarea = wrapper.find('.prompt-textarea')
    await textarea.setValue('Updated prompt content')

    const saveButton = wrapper.findAll('button').find(b => b.text().includes('保存') && !b.text().includes('隐藏'))
    if (saveButton) {
      await saveButton.trigger('click')
    }

    await flushPromises()

    // Calculate expected content (generatedMarkdown output)
    const expectedContent = `---\nname: existing-skill\ndescription: Existing description\n---\n\nUpdated prompt content`

    // Verify PUT was called with content field
    expect(mockPut).toHaveBeenCalled()
    const [, updatePayload] = mockPut.mock.calls[0]
    expect(updatePayload.content).toBe(expectedContent)
  })

  it('should not have model field in preview', async () => {
    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    const nameInput = wrapper.find('input[type="text"]')
    await nameInput.setValue('test-skill')

    const textarea = wrapper.find('.prompt-textarea')
    await textarea.setValue('Test prompt content')

    const previewContent = wrapper.find('.code-block').text()
    expect(previewContent).not.toContain('model:')
  })

  it('should not include model in create payload', async () => {
    mockPost.mockResolvedValueOnce({ status: 201 })

    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    const nameInput = wrapper.find('input[type="text"]')
    await nameInput.setValue('new-skill')

    const textarea = wrapper.find('.prompt-textarea')
    await textarea.setValue('Test prompt content')

    const saveButton = wrapper.findAll('button').find(b => b.text().includes('保存') && !b.text().includes('隐藏'))
    if (saveButton) {
      await saveButton.trigger('click')
    }

    await flushPromises()

    expect(mockPost).toHaveBeenCalled()
    const [, createPayload] = mockPost.mock.calls[0]
    expect(createPayload).not.toHaveProperty('model')
  })

  it('should not include model in update payload', async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        name: 'existing-skill',
        description: 'Existing description',
        model: 'deepseek-chat',
        inputs: [],
        prompt: 'Existing prompt',
      }
    })
    mockPut.mockResolvedValueOnce({ status: 200 })

    await router.push('/skills/existing-skill')
    await router.isReady()

    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    await flushPromises()

    const textarea = wrapper.find('.prompt-textarea')
    await textarea.setValue('Updated prompt content')

    const saveButton = wrapper.findAll('button').find(b => b.text().includes('保存') && !b.text().includes('隐藏'))
    if (saveButton) {
      await saveButton.trigger('click')
    }

    await flushPromises()

    expect(mockPut).toHaveBeenCalled()
    const [, updatePayload] = mockPut.mock.calls[0]
    expect(updatePayload).not.toHaveProperty('model')
  })
})

describe('SkillEditor Load', () => {
  let router: ReturnType<typeof createTestRouter>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(async () => {
    router = createTestRouter()
    pinia = createPinia()
    vi.clearAllMocks()
  })

  it('should load existing skill data', async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        name: 'test-skill',
        description: 'Test description',
        model: 'deepseek-chat',
        inputs: [
          { name: 'text', description: 'Input text', required: true, default: '' }
        ],
        prompt: 'Process: {{text}}',
      }
    })

    await router.push('/skills/test-skill')
    await router.isReady()

    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    await flushPromises()

    expect(mockGet).toHaveBeenCalledWith('/api/v1/skills/test-skill')
    expect(wrapper.find('input[type="text"]').element.value).toBe('test-skill')
  })

  it('should redirect to skills list when load fails', async () => {
    mockGet.mockRejectedValueOnce(new Error('Not found'))
    const pushSpy = vi.spyOn(router, 'push')
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})

    await router.push('/skills/nonexistent')
    await router.isReady()

    mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    await flushPromises()

    expect(alertSpy).toHaveBeenCalledWith('加载技能失败')
    expect(pushSpy).toHaveBeenCalledWith('/skills')

    alertSpy.mockRestore()
  })

  it('should disable name input when editing', async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        name: 'test-skill',
        description: 'Test description',
        model: 'deepseek-chat',
        inputs: [],
        prompt: 'Test prompt',
      }
    })

    await router.push('/skills/test-skill')
    await router.isReady()

    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    await flushPromises()

    const nameInput = wrapper.find('input[type="text"]')
    expect(nameInput.attributes('disabled')).toBeDefined()
  })
})

describe('SkillEditor Navigation', () => {
  let router: ReturnType<typeof createTestRouter>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(async () => {
    router = createTestRouter()
    pinia = createPinia()
    await router.push('/skills/new')
    await router.isReady()
    vi.clearAllMocks()
  })

  it('should navigate back to skills list', async () => {
    const pushSpy = vi.spyOn(router, 'push')

    const wrapper = mount(SkillEditor, {
      global: {
        plugins: [router, pinia]
      }
    })

    const backButton = wrapper.find('.btn-back')
    await backButton.trigger('click')

    expect(pushSpy).toHaveBeenCalledWith('/skills')
  })
})
