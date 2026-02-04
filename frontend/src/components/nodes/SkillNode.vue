<template>
  <div class="node skill-node">
    <div class="node-header">
      <span class="node-icon">🎯</span>
      <span class="node-title">Skill</span>
    </div>
    <div class="node-body">
      <span class="node-desc">{{ skillDisplayName }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
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

<style scoped>
.skill-node {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  border-radius: 8px;
  padding: 12px 16px;
  min-width: 140px;
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
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
