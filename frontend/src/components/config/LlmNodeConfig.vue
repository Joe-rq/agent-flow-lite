<template>
  <div class="config-section">
    <h4>LLM 节点</h4>

    <!-- 技能选择 -->
    <div class="form-group">
      <label>加载技能 (可选)</label>
      <SelectInput
        :model-value="config.skillName"
        :options="skills.map(skill => ({ value: skill.name, label: skill.name }))"
        placeholder="不使用技能"
        @update:model-value="updateField('skillName', $event); $emit('skill-change')"
      />
      <small class="form-hint">选择技能将自动加载其提示词和模型配置</small>
    </div>

    <div class="form-group">
      <label>模型</label>
      <SelectInput
        :model-value="config.model || ''"
        :options="models.map(item => ({ value: item.id, label: `${item.provider} / ${item.model}` }))"
        placeholder="跟随默认模型"
        @update:model-value="updateField('model', $event)"
      />
      <small class="form-hint">未选择时使用系统默认模型</small>
    </div>

    <div class="form-group">
      <label class="checkbox-label">
        <input
          :checked="!!config.inheritChatHistory"
          type="checkbox"
          @change="updateField('inheritChatHistory', ($event.target as HTMLInputElement).checked)"
        />
        继承会话历史
      </label>
      <small class="form-hint">开启后，节点会携带当前会话历史上下文执行</small>
    </div>

    <!-- 系统提示词 -->
    <div class="form-group">
      <label>系统提示词</label>
      <TextArea
        :model-value="config.systemPrompt ?? ''"
        :rows="6"
        :placeholder="hints?.systemPrompt?.placeholder"
        :disabled="!!config.skillName"
        @update:model-value="updateField('systemPrompt', $event)"
      />
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
import type { AvailableModel, NodeConfig, Skill } from '@/composables/workflow/useNodeConfig'
import { SelectInput, TextArea } from '@/components/ui'
import { fieldHints } from './nodeHelpData'

const hints = fieldHints.llm

const props = defineProps<{
  config: NodeConfig
  skills: Skill[]
  models: AvailableModel[]
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
