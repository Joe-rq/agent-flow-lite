<template>
  <div class="config-section">
    <h4>技能节点</h4>
    <div class="form-group">
      <label>选择技能</label>
      <select v-model="config.skillName" class="form-select" @change="$emit('skill-change')">
        <option value="">请选择技能</option>
        <option v-for="skill in skills" :key="skill.name" :value="skill.name">
          {{ skill.name }}
        </option>
      </select>
      <small class="form-hint">{{ hints?.skillName?.hint }}</small>
    </div>
    <div v-if="selectedSkillInputs.length > 0" class="form-group">
      <label>输入映射</label>
      <div v-for="input in selectedSkillInputs" :key="input.name" class="input-mapping-row">
        <span class="input-name">{{ input.name }}</span>
        <select
          v-model="(config.inputMappings || {})[input.name]"
          class="form-select mapping-select"
        >
          <option value="">自动映射</option>
          <option v-for="node in upstreamNodes" :key="node.id" :value="node.id">
            {{ node.label || node.id }}
          </option>
        </select>
      </div>
      <small class="form-hint">选择上游节点作为输入来源，或留空自动映射</small>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { NodeConfig, Skill, WorkflowNode } from '@/composables/workflow/useNodeConfig'
import { fieldHints } from './nodeHelpData'

const hints = fieldHints.skill

defineProps<{
  config: NodeConfig
  skills: Skill[]
  selectedSkillInputs: Array<{ name: string; label?: string; required?: boolean }>
  upstreamNodes: WorkflowNode[]
}>()

defineEmits<{
  'skill-change': []
}>()
</script>

<style src="./node-config-form.css"></style>
