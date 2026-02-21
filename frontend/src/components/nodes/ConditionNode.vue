<template>
  <div class="flow-node-base min-w-[160px] border-t-[3px] border-t-pink-500 shadow-lg shadow-pink-500/10 dark:shadow-pink-500/30
    [&_.vue-flow__handle]:w-2 [&_.vue-flow__handle]:h-2 [&_.vue-flow__handle]:bg-white [&_.vue-flow__handle]:border-2 [&_.vue-flow__handle]:border-pink-500
    [&_.handle-true]:border-emerald-500 [&_.handle-false]:border-red-500"
  >
    <div class="flex items-center gap-2 mb-1">
      <span class="w-5 h-5 flex items-center justify-center rounded text-xs bg-pink-500/10 text-pink-600">⚡</span>
      <span class="text-sm font-semibold text-card-foreground">条件</span>
    </div>
    <div class="text-xs text-muted-foreground truncate max-w-[140px]">{{ expression || '点击配置条件' }}</div>
    <Handle type="target" :position="Position.Left" />
    <Handle type="source" :position="Position.Right" id="true" class="handle-true">
      <span class="absolute left-3 top-1/2 -translate-y-1/2 text-[10px] font-semibold pointer-events-none whitespace-nowrap text-emerald-500">True</span>
    </Handle>
    <Handle type="source" :position="Position.Bottom" id="false" class="handle-false">
      <span class="absolute top-3 left-1/2 -translate-x-1/2 text-[10px] font-semibold pointer-events-none whitespace-nowrap text-red-500">False</span>
    </Handle>
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


