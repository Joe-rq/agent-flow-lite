import { ref, computed } from 'vue'
import axios from 'axios'
import { API_BASE } from '@/utils/constants'
import { useToast } from '@/composables/useToast'

export interface TokenUsageSummary {
  total_input_tokens: number
  total_output_tokens: number
  total_requests: number
  by_provider: Record<string, ProviderUsage>
  by_model: Record<string, ModelUsage>
}

export interface ProviderUsage {
  input_tokens: number
  output_tokens: number
  requests: number
}

export interface ModelUsage {
  input_tokens: number
  output_tokens: number
  requests: number
}

export type TimeRange = '24h' | '7d' | '30d'

const HOURS_MAP: Record<TimeRange, number> = {
  '24h': 24,
  '7d': 168,
  '30d': 720,
}

// Approximate cost per 1K tokens (input/output) in USD
const COST_PER_1K: Record<string, { input: number; output: number }> & {
  default: { input: number; output: number }
} = {
  'deepseek-chat': { input: 0.00014, output: 0.00028 },
  'deepseek-coder': { input: 0.00014, output: 0.00028 },
  default: { input: 0.0015, output: 0.002 },
}

export function useDashboard() {
  const { showToast } = useToast()

  const data = ref<TokenUsageSummary | null>(null)
  const timeRange = ref<TimeRange>('24h')
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const totalTokens = computed(() => {
    if (!data.value) return 0
    return data.value.total_input_tokens + data.value.total_output_tokens
  })

  const estimatedCost = computed(() => {
    if (!data.value) return 0
    let cost = 0
    const defaultRates = COST_PER_1K.default
    for (const [model, usage] of Object.entries(data.value.by_model)) {
      const rates = COST_PER_1K[model] ?? defaultRates
      cost += (usage.input_tokens / 1000) * rates.input
      cost += (usage.output_tokens / 1000) * rates.output
    }
    return cost
  })

  const providerList = computed(() => {
    if (!data.value) return []
    return Object.entries(data.value.by_provider)
      .map(([name, usage]) => ({
        name,
        ...usage,
        total: usage.input_tokens + usage.output_tokens,
      }))
      .sort((a, b) => b.total - a.total)
  })

  const modelList = computed(() => {
    if (!data.value) return []
    return Object.entries(data.value.by_model)
      .map(([name, usage]) => ({
        name,
        ...usage,
        total: usage.input_tokens + usage.output_tokens,
      }))
      .sort((a, b) => b.total - a.total)
  })

  async function fetchTokenUsage() {
    isLoading.value = true
    error.value = null
    try {
      const hours = HOURS_MAP[timeRange.value]
      const response = await axios.get(`${API_BASE}/observability/token-usage`, {
        params: { hours },
      })
      data.value = response.data
    } catch (err: any) {
      console.error('Failed to fetch token usage:', err)
      const errorMsg = err.response?.data?.detail || 'Failed to fetch token usage'
      error.value = errorMsg
      showToast(errorMsg)
    } finally {
      isLoading.value = false
    }
  }

  function setTimeRange(range: TimeRange) {
    timeRange.value = range
    fetchTokenUsage()
  }

  return {
    data,
    timeRange,
    isLoading,
    error,
    totalTokens,
    estimatedCost,
    providerList,
    modelList,
    fetchTokenUsage,
    setTimeRange,
  }
}
