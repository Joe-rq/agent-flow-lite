<template>
  <div class="node condition-node">
    <div class="node-header">
      <span class="node-icon">⚡</span>
      <span class="node-title">条件</span>
    </div>
    <div class="node-body">
      <span class="node-desc">{{ expression || '点击配置条件' }}</span>
    </div>
    <Handle type="target" :position="Position.Left" />
    <Handle type="source" :position="Position.Right" id="true" class="handle-true" />
    <Handle type="source" :position="Position.Bottom" id="false" class="handle-false" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Handle, Position } from '@vue-flow/core'

const props = defineProps<{
  data?: {
    expression?: string
  }
}>()

const expression = computed(() => {
  return props.data?.expression || ''
})
</script>

<script lang="ts">
export default {
  inheritAttrs: false,
}
</script>

<style scoped>
.condition-node {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
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
  color: rgba(255, 255, 255, 0.8);
  display: block;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.vue-flow__handle) {
  width: 8px;
  height: 8px;
  background: white;
  border: 2px solid #d97706;
}

:deep(.handle-true) {
  border-color: #10b981;
}

:deep(.handle-false) {
  border-color: #ef4444;
}
</style>
