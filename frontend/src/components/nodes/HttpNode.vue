<template>
  <div class="flow-node-base min-w-[160px] border-t-[3px] border-t-orange-500 shadow-lg shadow-orange-500/10 dark:shadow-orange-500/30">
    <div class="flex items-center gap-2 mb-1">
      <span class="w-5 h-5 flex items-center justify-center rounded text-xs bg-orange-500/10 text-orange-600">🌐</span>
      <span class="text-sm font-semibold text-card-foreground">HTTP</span>
    </div>
    <div class="text-xs text-muted-foreground truncate max-w-[140px]">{{ displayText }}</div>
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


