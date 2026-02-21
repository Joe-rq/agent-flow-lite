<template>
  <div class="flow-node-base border-t-[3px] border-t-violet-500 shadow-lg shadow-violet-500/10 dark:shadow-violet-500/30">
    <div class="flex items-center gap-2 mb-1">
      <span class="w-5 h-5 flex items-center justify-center rounded text-xs bg-violet-500/10 text-violet-600">🤖</span>
      <span class="text-sm font-semibold text-card-foreground">LLM</span>
    </div>
    <div class="text-xs text-muted-foreground">{{ displayText }}</div>
  </div>
</template>

<script setup lang="ts">
// Node component - Handle and Position imported for future use
import { computed } from 'vue'

interface Props {
  data?: {
    skillName?: string
    model?: string
    systemPrompt?: string
  }
}

const props = defineProps<Props>()

const displayText = computed(() => {
  if (props.data?.skillName) {
    return `Skill: ${props.data.skillName}`
  }
  if (props.data?.model) {
    return `Model: ${props.data.model}`
  }
  return 'AI 模型调用'
})
</script>

<script lang="ts">
export default {
  inheritAttrs: false,
}
</script>


