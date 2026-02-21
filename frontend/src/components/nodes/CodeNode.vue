<template>
  <div class="flow-node-base border-t-[3px] border-t-slate-500 shadow-lg shadow-slate-500/10 dark:shadow-slate-500/30">
    <div class="flex items-center gap-2 mb-1">
      <span class="w-5 h-5 flex items-center justify-center rounded text-xs bg-slate-500/10 text-slate-600">🧪</span>
      <span class="text-sm font-semibold text-card-foreground">Code</span>
    </div>
    <div class="text-xs text-muted-foreground">{{ displayText }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  data?: {
    code?: string
    timeoutSeconds?: number
  }
}

const props = defineProps<Props>()

const displayText = computed(() => {
  if (props.data?.code?.trim()) {
    return `Timeout: ${props.data.timeoutSeconds ?? 30}s`
  }
  return 'Python execution'
})
</script>

<script lang="ts">
export default {
  inheritAttrs: false,
}
</script>


