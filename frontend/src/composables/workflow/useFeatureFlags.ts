import { computed, ref } from 'vue'
import axios from 'axios'

export function useFeatureFlags() {
  const featureFlags = ref<Record<string, boolean>>({})

  const enabledNodeTypes = computed(() => {
    const base = ['start', 'llm', 'knowledge', 'condition', 'skill', 'end']
    if (featureFlags.value.ENABLE_HTTP_NODE) {
      base.splice(base.length - 1, 0, 'http')
    }
    if (featureFlags.value.ENABLE_CODE_NODE) {
      base.splice(base.length - 1, 0, 'code')
    }
    return base
  })

  async function loadFeatureFlags() {
    try {
      const response = await axios.get('/api/v1/settings/feature-flags')
      const items = Array.isArray(response.data?.items) ? response.data.items : []
      const nextFlags: Record<string, boolean> = {}
      for (const item of items) {
        if (typeof item?.key === 'string') {
          nextFlags[item.key] = Boolean(item.enabled)
        }
      }
      featureFlags.value = nextFlags
    } catch (error) {
      console.error('加载功能开关失败:', error)
      featureFlags.value = {}
    }
  }

  return { enabledNodeTypes, loadFeatureFlags }
}
