<template>
  <div class="settings-view">
    <div class="settings-card">
      <h2>模型设置</h2>
      <p class="hint">设置默认模型后，聊天会优先使用该模型。</p>

      <div v-if="isLoading" class="state">加载中...</div>
      <div v-else-if="errorMessage" class="state error">{{ errorMessage }}</div>
      <div v-else-if="models.length === 0" class="state">当前没有可用模型，请先配置 API Key。</div>
      <div v-else class="form-group">
        <label for="default-model">默认模型</label>
        <select id="default-model" v-model="selectedModel" @change="saveSelection">
          <option v-for="item in models" :key="item.id" :value="item.id">
            {{ item.provider }} / {{ item.model }}
          </option>
        </select>
      </div>
    </div>

    <div class="settings-card">
      <h2>功能开关</h2>
      <p class="hint">高风险能力默认关闭，管理员可运行时开启或熔断。</p>

      <div v-if="!authStore.isAdmin" class="state">仅管理员可修改功能开关。</div>
      <div v-else-if="flagErrorMessage" class="state error">{{ flagErrorMessage }}</div>
      <div v-else-if="featureFlags.length === 0" class="state">暂无可配置开关。</div>
      <div v-else class="flag-list">
        <label v-for="item in featureFlags" :key="item.key" class="flag-item">
          <span>{{ item.key }}</span>
          <input
            type="checkbox"
            :checked="item.enabled"
            :disabled="!!updatingKeys[item.key]"
            @change="toggleFeatureFlag(item.key, $event)"
          />
        </label>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

interface ModelItem {
  id: string
  provider: string
  model: string
}

interface FeatureFlagItem {
  key: string
  enabled: boolean
}

const STORAGE_KEY = 'agent-flow.default-model'
const authStore = useAuthStore()

const models = ref<ModelItem[]>([])
const selectedModel = ref('')
const isLoading = ref(false)
const errorMessage = ref('')
const featureFlags = ref<FeatureFlagItem[]>([])
const flagErrorMessage = ref('')
const updatingKeys = ref<Record<string, boolean>>({})

async function loadModels() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const response = await axios.get('/api/v1/chat/models')
    models.value = Array.isArray(response.data?.items) ? response.data.items : []

    const stored = window.localStorage.getItem(STORAGE_KEY)
    const backendDefault = response.data?.default_model || ''
    const preferred = stored || backendDefault
    const hasPreferred = models.value.some((item) => item.id === preferred)

    if (hasPreferred) {
      selectedModel.value = preferred
    } else if (models.value.length > 0) {
      const firstModel = models.value[0]
      if (firstModel) {
        selectedModel.value = firstModel.id
        window.localStorage.setItem(STORAGE_KEY, selectedModel.value)
      }
    }
  } catch (error) {
    console.error('加载模型列表失败:', error)
    errorMessage.value = '加载模型列表失败'
  } finally {
    isLoading.value = false
  }
}

function saveSelection() {
  if (!selectedModel.value) {
    return
  }
  window.localStorage.setItem(STORAGE_KEY, selectedModel.value)
}

async function loadFeatureFlags() {
  if (!authStore.isAdmin) {
    featureFlags.value = []
    return
  }

  flagErrorMessage.value = ''
  try {
    const response = await axios.get('/api/v1/settings/feature-flags')
    const items = Array.isArray(response.data?.items) ? response.data.items : []
    featureFlags.value = items
      .filter((item: unknown): item is FeatureFlagItem => {
        if (!item || typeof item !== 'object') {
          return false
        }
        const maybe = item as FeatureFlagItem
        return typeof maybe.key === 'string' && typeof maybe.enabled === 'boolean'
      })
      .sort((a: FeatureFlagItem, b: FeatureFlagItem) => a.key.localeCompare(b.key))
  } catch (error) {
    console.error('加载功能开关失败:', error)
    flagErrorMessage.value = '加载功能开关失败'
  }
}

async function toggleFeatureFlag(flagKey: string, event: Event) {
  const target = event.target as HTMLInputElement
  const enabled = !!target.checked
  updatingKeys.value = { ...updatingKeys.value, [flagKey]: true }
  try {
    await axios.put(`/api/v1/settings/feature-flags/${flagKey}`, { enabled })
    featureFlags.value = featureFlags.value.map((item) => {
      if (item.key === flagKey) {
        return { ...item, enabled }
      }
      return item
    })
  } catch (error) {
    console.error('更新功能开关失败:', error)
    target.checked = !enabled
  } finally {
    const next = { ...updatingKeys.value }
    delete next[flagKey]
    updatingKeys.value = next
  }
}

onMounted(() => {
  loadModels()
  loadFeatureFlags()
})
</script>

<style scoped>
.settings-view {
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  justify-content: center;
}

.settings-card {
  width: 100%;
  max-width: 560px;
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  background: var(--bg-secondary);
  padding: 20px;
}

.settings-card h2 {
  margin-bottom: 8px;
}

.hint {
  color: var(--text-secondary);
  margin-bottom: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

select {
  height: 36px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-secondary);
  background: var(--bg-primary);
  color: var(--text-primary);
  padding: 0 12px;
}

.state {
  color: var(--text-secondary);
}

.state.error {
  color: var(--accent-red);
}

.flag-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.flag-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
}
</style>
