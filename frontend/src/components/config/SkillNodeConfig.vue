<template>
  <div class="config-section">
    <h4>技能节点</h4>
    <div class="form-group">
      <label>选择技能</label>
      <SelectInput
        :model-value="config.skillName"
        :options="skills.map(skill => ({ value: skill.name, label: skill.name }))"
        placeholder="请选择技能"
        @update:model-value="updateField('skillName', $event); $emit('skill-change')"
      />
      <small class="form-hint">{{ hints?.skillName?.hint }}</small>
    </div>
    <div v-if="selectedSkillInputs.length > 0" class="form-group">
      <label>输入映射</label>
      <div v-for="input in selectedSkillInputs" :key="input.name" class="input-mapping-row">
        <span class="input-name">{{ input.name }}</span>
        <SelectInput
          :model-value="(config.inputMappings || {})[input.name]"
          :options="upstreamNodes.map(node => ({ value: node.id, label: node.label || node.id }))"
          placeholder="自动映射"
          @update:model-value="updateMapping(input.name, String($event))"
        />
      </div>
      <small class="form-hint">选择上游节点作为输入来源，或留空自动映射</small>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { NodeConfig, Skill, WorkflowNode } from '@/composables/workflow/useNodeConfig'
import { SelectInput } from '@/components/ui'
import { fieldHints } from './nodeHelpData'

const hints = fieldHints.skill

const props = defineProps<{
  config: NodeConfig
  skills: Skill[]
  selectedSkillInputs: Array<{ name: string; label?: string; required?: boolean }>
  upstreamNodes: WorkflowNode[]
}>()

const emit = defineEmits<{
  'skill-change': []
  'update:config': [value: NodeConfig]
}>()

function updateField(field: string, value: unknown) {
  emit('update:config', { ...props.config, [field]: value })
}

function updateMapping(inputName: string, nodeId: string) {
  const mappings = { ...(props.config.inputMappings || {}), [inputName]: nodeId }
  emit('update:config', { ...props.config, inputMappings: mappings })
}
</script>

<style src="./node-config-form.css"></style>
