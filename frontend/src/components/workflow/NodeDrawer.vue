<template>
  <!-- 抽屉切换按钮 -->
  <button
    class="drawer-toggle"
    :class="{ 'drawer-open': showDrawer }"
    @click="$emit('toggle')"
    :title="showDrawer ? '收起面板' : '展开面板'"
  >
    <span class="toggle-icon">{{ showDrawer ? '▶' : '◀' }}</span>
  </button>

  <!-- 节点创建抽屉 -->
  <div class="node-drawer" :class="{ open: showDrawer }">
    <h3 class="drawer-title">添加节点</h3>
    <div class="drawer-content">
      <div
        v-for="node in visibleNodeTypes"
        :key="node.type"
        class="drawer-node-item"
        draggable="true"
        @dragstart="$emit('drag-start', $event, node.type)"
        @click="$emit('add-node', node.type)"
      >
        <span class="drawer-node-icon">{{ node.icon }}</span>
        <span class="drawer-node-label">{{ node.label }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const nodeTypes = [
  { type: 'start', icon: '▶', label: '开始节点' },
  { type: 'llm', icon: '🤖', label: 'LLM 节点' },
  { type: 'knowledge', icon: '📚', label: '知识库节点' },
  { type: 'condition', icon: '⚡', label: '条件节点' },
  { type: 'skill', icon: '🎯', label: '技能节点' },
  { type: 'http', icon: '🌐', label: 'HTTP 节点' },
  { type: 'code', icon: '🧪', label: '代码节点' },
  { type: 'end', icon: '⏹', label: '结束节点' },
]

const props = withDefaults(defineProps<{
  showDrawer: boolean
  enabledNodeTypes?: string[]
}>(), {
  enabledNodeTypes: () => ['start', 'llm', 'knowledge', 'condition', 'skill', 'end'],
})

const visibleNodeTypes = computed(() => {
  const allowed = new Set(props.enabledNodeTypes)
  return nodeTypes.filter((item) => allowed.has(item.type))
})

defineEmits<{
  'add-node': [type: string]
  'drag-start': [event: DragEvent, type: string]
  toggle: []
}>()
</script>

<style scoped src="./NodeDrawer.css"></style>
