<template>
  <div v-if="showRunModal" class="dialog-overlay" @click.self="$emit('close')">
    <div class="dialog run-dialog">
      <div class="dialog-header">
        <h3>运行技能: {{ runningSkill?.name }}</h3>
        <button class="btn-close" @click="$emit('close')">×</button>
      </div>

      <!-- 输入表单 -->
      <div class="run-inputs">
        <div
          v-for="input in runningSkill?.inputs"
          :key="input.name"
          class="form-group"
        >
          <label>
            {{ input.name }}
            <span v-if="input.required" class="required-mark">*</span>
          </label>
          <input
            v-model="runInputs[input.name]"
            type="text"
            :placeholder="input.description || `请输入 ${input.name}`"
          />
        </div>
      </div>

      <!-- 运行按钮 -->
      <div class="dialog-actions">
        <button
          class="btn-secondary"
          @click="$emit('close')"
          :disabled="isRunning"
        >
          取消
        </button>
        <button
          class="btn-primary"
          :disabled="isRunning"
          @click="$emit('run')"
        >
          {{ isRunning ? '运行中...' : '运行' }}
        </button>
      </div>

      <!-- 输出区域 -->
      <div v-if="runOutput || isRunning" class="run-output">
        <div class="output-header">
          <span>输出</span>
          <span v-if="isRunning" class="running-indicator">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </span>
        </div>
        <div class="output-content" ref="outputEl">
          <div v-if="currentThought" class="thought-line">
            <span class="thought-icon">💭</span>
            <span class="thought-text">{{ currentThought }}</span>
          </div>
          <div class="output-text">{{ runOutput }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import type { Skill } from '@/types'

const props = defineProps<{
  showRunModal: boolean
  runningSkill: Skill | null
  runInputs: Record<string, string>
  runOutput: string
  isRunning: boolean
  currentThought: string
}>()

defineEmits<{
  close: []
  run: []
}>()

const outputEl = ref<HTMLElement | null>(null)

function scrollToBottom() {
  nextTick(() => {
    if (outputEl.value) {
      outputEl.value.scrollTop = outputEl.value.scrollHeight
    }
  })
}

watch(() => props.runOutput, scrollToBottom)
watch(() => props.currentThought, scrollToBottom)
</script>

<style scoped src="./SkillRunDialog.css"></style>
