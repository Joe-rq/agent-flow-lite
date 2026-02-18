import { ref, nextTick, type Ref, type ComputedRef } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { createSSEParser } from '@/utils/sse-parser'
import { useToast } from '@/composables/useToast'
import type { CitationSource, Message, Session } from './types'
import { handleSSEEventDispatch } from './sseEventHandlers'

interface UseChatSSEOptions {
  currentSession: ComputedRef<Session | undefined>
  currentSessionId: Ref<string>
  selectedWorkflowId: Ref<string>
  selectedKbId: Ref<string>
  messagesContainer: Ref<HTMLElement | null>
  activeCitation: Ref<CitationSource | null>
  createNewSession: () => void
}

const SSE_TIMEOUT_MS = 180_000
const DEFAULT_MODEL_STORAGE_KEY = 'agent-flow.default-model'

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

export function useChatSSE(options: UseChatSSEOptions) {
  const {
    currentSession,
    currentSessionId,
    selectedWorkflowId,
    selectedKbId,
    messagesContainer,
    activeCitation,
    createNewSession,
  } = options

  const isStreaming = ref(false)
  const currentThought = ref('')
  const authStore = useAuthStore()
  const { showToast } = useToast()
  let abortController: AbortController | null = null

  function scrollToBottom() {
    nextTick(() => {
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      }
    })
  }

  function buildChatPayload(sessionId: string, message: string) {
    const model = window.localStorage.getItem(DEFAULT_MODEL_STORAGE_KEY) || undefined
    return {
      session_id: sessionId,
      message: message,
      workflow_id: selectedWorkflowId.value || undefined,
      kb_id: selectedKbId.value || undefined,
      model,
    }
  }

  const eventCtx = { isStreaming, currentThought, scrollToBottom }

  function handleSSEEvent(
    eventType: string,
    data: Record<string, unknown>,
    lastMessage: Message | undefined,
  ) {
    handleSSEEventDispatch(eventType, data, lastMessage, eventCtx)
  }

  async function connectSSE(sessionId: string, message: string) {
    abortController = new AbortController()
    let timeoutId = setTimeout(() => abortController?.abort(), SSE_TIMEOUT_MS)
    function resetTimeout() {
      clearTimeout(timeoutId)
      timeoutId = setTimeout(() => abortController?.abort(), SSE_TIMEOUT_MS)
    }
    const payload = buildChatPayload(sessionId, message)
    const response = await fetch('/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.token}`,
      },
      body: JSON.stringify(payload),
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

    const session = currentSession.value!
    const lastMessage = session.messages[session.messages.length - 1]
    const sseParser = createSSEParser()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      sseParser.parse(chunk, {
        onEvent: (eventType, eventData) => {
          resetTimeout()
          handleSSEEvent(eventType, eventData, lastMessage)
        },
        onComment: () => resetTimeout(),
        onDone: () => {
          isStreaming.value = false
          if (lastMessage) lastMessage.isStreaming = false
          currentThought.value = ''
        },
      })
    }

    isStreaming.value = false
    if (lastMessage) lastMessage.isStreaming = false
    currentThought.value = ''
    activeCitation.value = null
    abortController = null
    clearTimeout(timeoutId)
  }

  async function sendMessage(inputMessageRef: Ref<string>) {
    const message = inputMessageRef.value.trim()
    if (!message || isStreaming.value) return

    if (!currentSession.value) {
      createNewSession()
    }

    const session = currentSession.value!
    session.messages.push({ role: 'user', content: message })

    if (session.messages.length === 1) {
      session.title = message.slice(0, 20) + (message.length > 20 ? '...' : '')
    }

    inputMessageRef.value = ''
    isStreaming.value = true
    currentThought.value = ''
    activeCitation.value = null

    session.messages.push({ role: 'assistant', content: '', isStreaming: true })
    scrollToBottom()

    try {
      await connectSSE(currentSessionId.value, message)
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') return
      console.error('SSE connection error:', error)
      const err = error as { message?: string }
      const lastMessage = session.messages[session.messages.length - 1]
      if (lastMessage && lastMessage.role === 'assistant') {
        lastMessage.content = '\u8FDE\u63A5\u9519\u8BEF: ' + (err.message || '\u8BF7\u91CD\u8BD5')
        lastMessage.isStreaming = false
      }
      isStreaming.value = false
      currentThought.value = ''
      showToast('发送消息失败: ' + (err.message || '请检查网络连接'))
    }

    session.updatedAt = Date.now()
  }

  function abort() {
    abortController?.abort()
  }

  return {
    isStreaming,
    currentThought,
    buildChatPayload,
    handleSSEEvent,
    sendMessage,
    connectSSE,
    scrollToBottom,
    abort,
  }
}
