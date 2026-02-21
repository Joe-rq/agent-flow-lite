<template>
  <div class="flow-node-base border-t-[3px] border-t-indigo-500 shadow-lg shadow-indigo-500/10 dark:shadow-indigo-500/30">
    <div class="flex items-center gap-2 mb-1">
      <span class="w-5 h-5 flex items-center justify-center rounded text-xs bg-indigo-500/10 text-indigo-600">🎯</span>
      <span class="text-sm font-semibold text-card-foreground">Skill</span>
    </div>
    <div class="text-xs text-muted-foreground truncate max-w-[120px]">{{ skillDisplayName }}</div>
  </div>
</template>

<script setup lang="ts">
// Node component - Handle and Position imported for future use
import { computed } from 'vue'

interface Props {
  data?: {
    skillName?: string
    inputMappings?: Record<string, string>
  }
}

const props = defineProps<Props>()

const skillDisplayName = computed(() => {
  return props.data?.skillName || '选择技能'
})
</script>

<script lang="ts">
export default {
  inheritAttrs: false,
}
</script>


