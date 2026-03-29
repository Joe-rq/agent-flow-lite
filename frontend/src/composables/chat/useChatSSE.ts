import { ref, nextTick, type Ref, type ComputedRef } from 'vue'
import { useSSEStream } from '@/composables/useSSEStream'
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

const DEFAULT_MODEL_STORAGE_KEY = 'agent-flow.default-model'

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

  const { isStreaming, fetchSSE, abort: abortSSE } = useSSEStream()
  const currentThought = ref('')
  const { showToast } = useToast()

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

    const lastMessage = session.messages[session.messages.length - 1]

    try {
      await fetchSSE({
        url: '/api/v1/chat/completions',
        body: buildChatPayload(currentSessionId.value, message),
        retry: { maxRetries: 2, baseDelayMs: 500, maxDelayMs: 5000 },
        onEvent: (eventType, data) => {
          handleSSEEvent(eventType, data, lastMessage)
        },
        onDone: () => {
          if (lastMessage) lastMessage.isStreaming = false
          currentThought.value = ''
        },
        onError: (err) => {
          if (lastMessage && lastMessage.role === 'assistant') {
            lastMessage.content = '连接错误: ' + (err.message || '请重试')
            lastMessage.isStreaming = false
          }
          currentThought.value = ''
          showToast('发送消息失败: ' + (err.message || '请检查网络连接'))
        },
      })
    } catch {
      // 错误已在 onError 中处理
    }

    session.updatedAt = Date.now()
  }

  function abort() {
    abortSSE()
  }

  return {
    isStreaming,
    currentThought,
    buildChatPayload,
    handleSSEEvent,
    sendMessage,
    scrollToBottom,
    abort,
  }
}
