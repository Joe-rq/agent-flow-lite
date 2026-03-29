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
        <SelectInput
          v-model="selectedModel"
          :options="models.map(item => ({ value: item.id, label: `${item.provider} / ${item.model}` }))"
          @update:model-value="saveSelection"
        />
      </div>
    </div>

    <div class="settings-card">
      <h2>嵌入模型配置</h2>
      <p class="hint">用于知识库文档向量化的模型配置。</p>

      <div v-if="embedLoading" class="state">加载中...</div>
      <div v-else-if="embedError" class="state error">{{ embedError }}</div>
      <div v-else class="embed-config">
        <div class="embed-info">
          <span class="embed-label">Provider:</span>
          <span class="embed-value">{{ embedProvider }}</span>
        </div>
        <div class="embed-info">
          <span class="embed-label">Model:</span>
          <span class="embed-value">{{ embedModel }}</span>
        </div>
        <div v-if="hasKnowledgeBases" class="warning-box">
          <strong>风险提示:</strong> 更改嵌入模型会导致新上传的文档与现有知识库向量维度不匹配，建议清空知识库后重新上传文档。
        </div>
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
import { SelectInput } from '@/components/ui'

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

const embedProvider = ref('')
const embedModel = ref('')
const embedLoading = ref(false)
const embedError = ref('')
const hasKnowledgeBases = ref(false)

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

async function loadEmbeddingConfig() {
  embedLoading.value = true
  embedError.value = ''
  try {
    const [embedRes, kbRes] = await Promise.all([
      axios.get('/api/v1/settings/embedding'),
      axios.get('/api/v1/knowledge'),
    ])
    embedProvider.value = embedRes.data?.provider || ''
    embedModel.value = embedRes.data?.model || ''
    hasKnowledgeBases.value = (kbRes.data?.total || 0) > 0
  } catch (error) {
    console.error('加载嵌入配置失败:', error)
    embedError.value = '加载嵌入配置失败'
  } finally {
    embedLoading.value = false
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
  loadEmbeddingConfig()
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
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-card);
  padding: 20px;
}

.settings-card h2 {
  margin-bottom: 8px;
}

.hint {
  color: var(--color-muted-foreground);
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
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-foreground);
  padding: 0 12px;
}

.state {
  color: var(--color-muted-foreground);
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
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-background);
}

.embed-config {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.embed-info {
  display: flex;
  gap: 8px;
}

.embed-label {
  color: var(--color-muted-foreground);
  min-width: 80px;
}

.embed-value {
  font-family: var(--font-mono);
}

.warning-box {
  padding: 12px;
  border: 1px solid var(--accent-amber, #f59e0b);
  border-radius: var(--radius-md);
  background: var(--accent-amber-bg, rgba(245, 158, 11, 0.1));
  color: var(--accent-amber-fg, #92400e);
  font-size: 14px;
  line-height: 1.5;
}
</style>
