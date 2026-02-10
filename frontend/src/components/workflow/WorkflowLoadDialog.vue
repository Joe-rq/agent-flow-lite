<template>
  <div v-if="showLoadDialog" class="dialog-overlay" @click.self="$emit('close')">
    <div class="dialog">
      <h3>加载工作流</h3>
      <div v-if="workflows.length === 0" class="empty-dialog">
        <p>暂无保存的工作流</p>
      </div>
      <div v-else class="workflow-list">
        <div
          v-for="workflow in workflows"
          :key="workflow.id"
          class="workflow-item"
          @click="$emit('load', workflow.id)"
        >
          <div class="workflow-name">{{ workflow.name }}</div>
          <div class="workflow-meta">创建于 {{ formatDate(workflow.created_at) }}</div>
        </div>
      </div>
      <div class="dialog-actions">
        <Button variant="secondary" @click="$emit('close')">关闭</Button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import Button from '@/components/ui/Button.vue'
import { formatDate } from '@/utils/format'
import type { WorkflowItem } from '@/composables/workflow/useWorkflowCrud'

defineProps<{
  showLoadDialog: boolean
  workflows: WorkflowItem[]
}>()

defineEmits<{
  load: [workflowId: string]
  close: []
}>()
</script>

<style scoped src="./WorkflowLoadDialog.css"></style>
