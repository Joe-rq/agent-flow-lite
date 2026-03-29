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
  retry?: RetryOptions
}

export interface RetryOptions {
  maxRetries: number // 默认 3
  baseDelayMs: number // 默认 1000ms
  maxDelayMs: number // 默认 10000ms
}

const SSE_TIMEOUT_MS = 300_000 // 5 min for workflow execution
const DEFAULT_RETRY: RetryOptions = {
  maxRetries: 3,
  baseDelayMs: 1000,
  maxDelayMs: 10000,
}

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

  function calculateDelay(attempt: number, options: RetryOptions): number {
    const delay = options.baseDelayMs * Math.pow(2, attempt)
    return Math.min(delay, options.maxDelayMs)
  }

  async function fetchSSE(options: SSEStreamOptions): Promise<void> {
    const authStore = useAuthStore()
    const { url, body, onEvent, onDone, onError, signal, retry } = options
    const retryOptions = retry ? { ...DEFAULT_RETRY, ...retry } : DEFAULT_RETRY

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
    let attempt = 0

    while (true) {
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
            onEvent: (eventType, data) => {
              resetTimeout()
              onEvent(eventType, data)
            },
            onComment: () => resetTimeout(),
            onDone: () => onDone?.(),
          })
        }
        // 成功完成，退出重试循环
        break
      } catch (error) {
        // 用户主动取消，不重试
        if (error instanceof DOMException && error.name === 'AbortError') {
          break
        }

        const err = error instanceof Error ? error : new Error(String(error))

        // 判断是否可重试（网络错误或 5xx 服务器错误）
        const isRetryable =
          err.message.includes('fetch') ||
          err.message.includes('network') ||
          err.message.includes('HTTP error! status: 5')

        if (isRetryable && attempt < retryOptions.maxRetries) {
          attempt++
          const delay = calculateDelay(attempt - 1, retryOptions)
          console.warn(`SSE 连接失败，${delay}ms 后重试 (${attempt}/${retryOptions.maxRetries})`)
          await new Promise((resolve) => setTimeout(resolve, delay))
          // 重新创建 AbortController
          abortController = new AbortController()
          timeoutId = setTimeout(() => abortController?.abort(), SSE_TIMEOUT_MS)
          continue
        }

        // 不可重试或重试次数耗尽
        onError?.(err)
        throw err
      } finally {
        clearTimeout(timeoutId)
        isStreaming.value = false
        abortController = null
      }
    }
  }

  function abort() {
    abortController?.abort()
  }

  return { isStreaming, fetchSSE, abort }
}
