<template>
  <div v-if="visible" class="dialog-overlay" @click.self="$emit('close')">
    <div class="dialog help-dialog">
      <div class="help-header">
        <h3>{{ example?.title }} — 配置示例</h3>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>

      <p class="help-desc">{{ example?.description }}</p>

      <div class="help-section">
        <div class="help-section-title">字段示例</div>
        <div v-for="field in example?.fields" :key="field.label" class="help-field">
          <span class="help-field-label">{{ field.label }}</span>
          <code class="help-field-value">{{ field.value }}</code>
        </div>
      </div>

      <div class="help-section">
        <div class="help-section-title">使用提示</div>
        <ul class="help-tips">
          <li v-for="(tip, i) in example?.tips" :key="i">{{ tip }}</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { nodeExamples } from './nodeHelpData'

const props = defineProps<{
  visible: boolean
  nodeType: string | null
}>()

defineEmits<{ close: [] }>()

const example = computed(() => (props.nodeType ? nodeExamples[props.nodeType] : null))
</script>

<style scoped src="./NodeHelpDialog.css"></style>
