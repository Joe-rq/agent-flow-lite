<template>
  <div class="node start-node">
    <div class="node-header">
      <span class="node-icon">▶</span>
      <span class="node-title">开始</span>
    </div>
    <div class="node-body">
      <span class="node-desc">工作流起点</span>
    </div>
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

<style scoped>
.start-node {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-radius: 8px;
  padding: 12px 16px;
  min-width: 140px;
  color: white;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
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
}
</style>
