import { ref, nextTick, type Ref, type ComputedRef } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { createSSEParser } from '@/utils/sse-parser'
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

  function scrollToBottom() {
    nextTick(() => {
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      }
    })
  }

  function buildChatPayload(sessionId: string, message: string) {
    return {
      session_id: sessionId,
      message: message,
      workflow_id: selectedWorkflowId.value || undefined,
      kb_id: selectedKbId.value || undefined,
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
    const payload = buildChatPayload(sessionId, message)
    const response = await fetch('/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.token}`,
      },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
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
          handleSSEEvent(eventType, eventData, lastMessage)
        },
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
      console.error('SSE connection error:', error)
      const err = error as { message?: string }
      const lastMessage = session.messages[session.messages.length - 1]
      if (lastMessage && lastMessage.role === 'assistant') {
        lastMessage.content = '\u8FDE\u63A5\u9519\u8BEF: ' + (err.message || '\u8BF7\u91CD\u8BD5')
        lastMessage.isStreaming = false
      }
      isStreaming.value = false
      currentThought.value = ''
      alert('\u53D1\u9001\u6D88\u606F\u5931\u8D25: ' + (err.message || '\u8BF7\u68C0\u67E5\u7F51\u7EDC\u8FDE\u63A5'))
    }

    session.updatedAt = Date.now()
  }

  return {
    isStreaming,
    currentThought,
    buildChatPayload,
    handleSSEEvent,
    sendMessage,
    connectSSE,
    scrollToBottom,
  }
}
