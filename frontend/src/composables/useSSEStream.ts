import { ref } from 'vue'
import { createSSEParser, type SSEEventData } from '@/utils/sse-parser'
import { useAuthStore } from '@/stores/auth'

export interface SSEStreamOptions {
  url: string
  body: Record<string, unknown>
  onEvent: (eventType: string, data: SSEEventData) => void
  onDone?: () => void
  onError?: (error: Error) => void
}

export function useSSEStream() {
  const isStreaming = ref(false)

  async function fetchSSE(options: SSEStreamOptions): Promise<void> {
    const authStore = useAuthStore()
    const { url, body, onEvent, onDone, onError } = options

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    if (authStore.token) {
      headers['Authorization'] = `Bearer ${authStore.token}`
    }

    isStreaming.value = true

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
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
          onEvent: (eventType, data) => onEvent(eventType, data),
          onDone: () => onDone?.(),
        })
      }
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error))
      onError?.(err)
      throw err
    } finally {
      isStreaming.value = false
    }
  }

  return { isStreaming, fetchSSE }
}
