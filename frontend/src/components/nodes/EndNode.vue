<template>
  <div class="flow-node-base border-t-[3px] border-t-red-500 shadow-lg shadow-red-500/10 dark:shadow-red-500/30">
    <div class="flex items-center gap-2 mb-1">
      <span class="w-5 h-5 flex items-center justify-center rounded text-xs bg-red-500/10 text-red-600">⏹</span>
      <span class="text-sm font-semibold text-card-foreground">结束</span>
    </div>
    <div class="text-xs text-muted-foreground">工作流终点</div>
    <Handle type="target" :position="Position.Left" />
  </div>
</template>

<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
</script>

<script lang="ts">
export default {
  inheritAttrs: false,
}
</script>


