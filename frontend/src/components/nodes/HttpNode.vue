<template>
  <div class="node http-node">
    <div class="node-header">
      <span class="node-icon">🌐</span>
      <span class="node-title">HTTP</span>
    </div>
    <div class="node-body">
      <span class="node-desc">{{ displayText }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  data?: {
    method?: string
    url?: string
  }
}

const props = defineProps<Props>()

const displayText = computed(() => {
  const method = (props.data?.method || 'GET').toUpperCase()
  const url = props.data?.url || ''
  if (url) {
    return `${method} ${url}`
  }
  return `${method} request`
})
</script>

<script lang="ts">
export default {
  inheritAttrs: false,
}
</script>

<style scoped>
.http-node {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  border-radius: 8px;
  padding: 12px 16px;
  min-width: 160px;
  color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04), 0 0 0 1px rgba(255, 255, 255, 0.1) inset;
}

.node-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
}

.node-icon {
  font-size: 12px;
}

.node-title {
  font-size: 14px;
}

.node-body {
  font-size: 12px;
  opacity: 0.9;
}

.node-desc {
  color: rgba(255, 255, 255, 0.9);
  display: block;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
