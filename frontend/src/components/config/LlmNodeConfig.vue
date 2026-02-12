<template>
  <div class="config-section">
    <h4>LLM 节点</h4>

    <!-- 技能选择 -->
    <div class="form-group">
      <label>加载技能 (可选)</label>
      <select :value="config.skillName" class="form-select" @change="updateField('skillName', ($event.target as HTMLSelectElement).value); $emit('skill-change')">
        <option value="">不使用技能</option>
        <option v-for="skill in skills" :key="skill.name" :value="skill.name">
          {{ skill.name }}
        </option>
      </select>
      <small class="form-hint">选择技能将自动加载其提示词和模型配置</small>
    </div>

    <!-- 系统提示词 -->
    <div class="form-group">
      <label>系统提示词</label>
      <textarea
        :value="config.systemPrompt"
        rows="6"
        :placeholder="hints?.systemPrompt?.placeholder"
        class="form-textarea"
        :disabled="!!config.skillName"
        @input="updateField('systemPrompt', ($event.target as HTMLTextAreaElement).value)"
      ></textarea>
      <small v-if="config.skillName" class="form-hint">提示词由技能提供，不可编辑</small>
      <small v-else class="form-hint">{{ hints?.systemPrompt?.hint }}</small>
    </div>

    <!-- 温度参数 -->
    <div class="form-group">
      <label>温度参数: {{ config.temperature }}</label>
      <input
        :value="config.temperature"
        type="range"
        min="0"
        max="1"
        step="0.1"
        class="form-range"
        :disabled="!!config.skillName"
        @input="updateField('temperature', Number(($event.target as HTMLInputElement).value))"
      />
      <div class="range-labels">
        <span>精确</span>
        <span>创意</span>
      </div>
      <small v-if="config.skillName" class="form-hint">温度参数由技能配置提供</small>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { NodeConfig, Skill } from '@/composables/workflow/useNodeConfig'
import { fieldHints } from './nodeHelpData'

const hints = fieldHints.llm

const props = defineProps<{
  config: NodeConfig
  skills: Skill[]
}>()

const emit = defineEmits<{
  'skill-change': []
  'update:config': [value: NodeConfig]
}>()

function updateField(field: string, value: unknown) {
  emit('update:config', { ...props.config, [field]: value })
}
</script>

<style src="./node-config-form.css"></style>
