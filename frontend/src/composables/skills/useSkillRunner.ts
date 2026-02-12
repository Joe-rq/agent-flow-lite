import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { createSSEParser } from '@/utils/sse-parser'
import { API_BASE } from '@/utils/constants'
import type { Skill } from '@/types'

const SSE_TIMEOUT_MS = 180_000

async function readErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json()
    if (body.detail) return String(body.detail)
  } catch {
    // not JSON
  }
  return `HTTP error! status: ${response.status}`
}

async function handle401() {
  const authStore = useAuthStore()
  authStore.clearAuth()
  const { default: router } = await import('@/router')
  router.push('/login')
}

export function useSkillRunner() {
  const showRunModal = ref(false)
  const runningSkill = ref<Skill | null>(null)
  const runInputs = ref<Record<string, string>>({})
  const runOutput = ref('')
  const isRunning = ref(false)
  const currentThought = ref('')

  const authStore = useAuthStore()
  let abortController: AbortController | null = null

  function openRunModal(skill: Skill) {
    runningSkill.value = skill
    runInputs.value = {}
    runOutput.value = ''
    currentThought.value = ''
    isRunning.value = false

    skill.inputs?.forEach((input) => {
      if (input.default) {
        runInputs.value[input.name] = input.default
      }
    })

    showRunModal.value = true
  }

  function closeRunModal() {
    if (isRunning.value) return
    showRunModal.value = false
    runningSkill.value = null
    runInputs.value = {}
    runOutput.value = ''
    currentThought.value = ''
  }

  function handleSSEEvent(eventType: string, data: Record<string, unknown>) {
    switch (eventType) {
      case 'thought':
        currentThought.value = (data.message as string) || (data.status as string) || ''
        break
      case 'token':
        runOutput.value += (data.content as string) || ''
        break
      case 'citation':
        if (data.sources && Array.isArray(data.sources) && data.sources.length > 0) {
          runOutput.value += '\n[引用 ' + data.sources.length + ' 个来源]'
        }
        break
      case 'done':
        isRunning.value = false
        currentThought.value = ''
        break
      case 'error':
        runOutput.value += '\n[错误: ' + (data.content || data.message || '未知错误') + ']'
        isRunning.value = false
        currentThought.value = ''
        break
    }
  }

  async function runSkill() {
    if (!runningSkill.value || isRunning.value) return

    const missingInputs = runningSkill.value.inputs?.filter(
      (input) => input.required && !runInputs.value[input.name]?.trim(),
    )
    if (missingInputs?.length) {
      alert(`请填写必填项: ${missingInputs.map((i) => i.name).join(', ')}`)
      return
    }

    isRunning.value = true
    runOutput.value = ''
    currentThought.value = ''
    abortController = new AbortController()
    const timeoutId = setTimeout(() => abortController?.abort(), SSE_TIMEOUT_MS)

    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      }
      if (authStore.token) {
        headers['Authorization'] = `Bearer ${authStore.token}`
      }

      const response = await fetch(`${API_BASE}/skills/${runningSkill.value.name}/run`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ inputs: runInputs.value }),
        signal: abortController.signal,
      })

      if (!response.ok) {
        if (response.status === 401) await handle401()
        const detail = await readErrorDetail(response)
        throw new Error(detail)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No response body')
      }

      const sseParser = createSSEParser()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })

        sseParser.parse(chunk, {
          onEvent: (eventType, data) => {
            handleSSEEvent(eventType, data)
          },
          onDone: () => {
            isRunning.value = false
            currentThought.value = ''
          },
        })
      }
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') return
      console.error('运行技能失败:', error)
      const err = error as { message?: string }
      runOutput.value += '\n[错误: ' + (err.message || '运行失败') + ']'
    } finally {
      clearTimeout(timeoutId)
      isRunning.value = false
      currentThought.value = ''
      abortController = null
    }
  }

  function abort() {
    abortController?.abort()
  }

  return {
    showRunModal,
    runningSkill,
    runInputs,
    runOutput,
    isRunning,
    currentThought,
    openRunModal,
    closeRunModal,
    runSkill,
    abort,
  }
}
