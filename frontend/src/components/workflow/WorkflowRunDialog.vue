<template>
  <div v-if="showRunDialog" class="dialog-overlay" @click.self="$emit('close')">
    <div class="dialog run-dialog">
      <h3>运行工作流</h3>
      <div class="run-meta">
        <span>工作流：</span>
        <strong>{{ workflowName }}</strong>
      </div>
      <textarea
        :value="runInput"
        class="run-input"
        placeholder="请输入测试输入"
        :disabled="isRunning"
        @input="$emit('update:runInput', ($event.target as HTMLTextAreaElement).value)"
      ></textarea>
      <div class="run-actions">
        <Button variant="default" @click="$emit('execute')" :disabled="isRunning">
          运行
        </Button>
        <Button variant="outline" @click="$emit('close')" :disabled="isRunning">
          关闭
        </Button>
      </div>
      <div class="run-output">
        <div class="run-section-title">输出</div>
        <pre>{{ runOutput }}</pre>
      </div>
      <div class="run-logs" v-if="runLogs.length">
        <div class="run-section-title">事件</div>
        <ul>
          <li v-for="(log, index) in runLogs" :key="index">{{ log }}</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import Button from '@/components/ui/Button.vue'

defineProps<{
  showRunDialog: boolean
  isRunning: boolean
  runInput: string
  runOutput: string
  runLogs: string[]
  workflowName: string
}>()

defineEmits<{
  'update:runInput': [value: string]
  execute: []
  close: []
}>()
</script>

<style scoped src="./WorkflowRunDialog.css"></style>
