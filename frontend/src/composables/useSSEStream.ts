import { ref } from 'vue'
import { createSSEParser, type SSEEventData } from '@/utils/sse-parser'
import { useAuthStore } from '@/stores/auth'

export interface SSEStreamOptions {
  url: string
  body: Record<string, unknown>
  onEvent: (eventType: string, data: SSEEventData) => void
  onDone?: () => void
  onError?: (error: Error) => void
  signal?: AbortSignal
}

const SSE_TIMEOUT_MS = 300_000 // 5 min for workflow execution

async function readErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json()
    if (body.detail) return String(body.detail)
  } catch {
    // response body not JSON, ignore
  }
  return `HTTP error! status: ${response.status}`
}

async function handle401() {
  const authStore = useAuthStore()
  authStore.clearAuth()
  const { default: router } = await import('@/router')
  router.push('/login')
}

export function useSSEStream() {
  const isStreaming = ref(false)
  let abortController: AbortController | null = null

  async function fetchSSE(options: SSEStreamOptions): Promise<void> {
    const authStore = useAuthStore()
    const { url, body, onEvent, onDone, onError, signal } = options

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    if (authStore.token) {
      headers['Authorization'] = `Bearer ${authStore.token}`
    }

    abortController = new AbortController()
    let timeoutId = setTimeout(() => abortController?.abort(), SSE_TIMEOUT_MS)
    function resetTimeout() {
      clearTimeout(timeoutId)
      timeoutId = setTimeout(() => abortController?.abort(), SSE_TIMEOUT_MS)
    }
    if (signal) {
      signal.addEventListener('abort', () => abortController?.abort(), { once: true })
    }

    isStreaming.value = true

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
        signal: abortController.signal,
      })

      if (!response.ok) {
        if (response.status === 401) await handle401()
        const detail = await readErrorDetail(response)
        throw new Error(detail)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No response body')
      }

      const decoder = new TextDecoder()
      const sseParser = createSSEParser()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        sseParser.parse(chunk, {
          onEvent: (eventType, data) => { resetTimeout(); onEvent(eventType, data) },
          onComment: () => resetTimeout(),
          onDone: () => onDone?.(),
        })
      }
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') return
      const err = error instanceof Error ? error : new Error(String(error))
      onError?.(err)
      throw err
    } finally {
      clearTimeout(timeoutId)
      isStreaming.value = false
      abortController = null
    }
  }

  function abort() {
    abortController?.abort()
  }

  return { isStreaming, fetchSSE, abort }
}
