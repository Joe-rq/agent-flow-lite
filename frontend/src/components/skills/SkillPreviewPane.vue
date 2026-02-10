<template>
  <div class="preview-pane">
    <div class="preview-header">
      <h3>预览</h3>
    </div>
    <div class="preview-content">
      <div class="preview-section">
        <h4>生成的 SKILL.md</h4>
        <pre class="code-block">{{ generatedMarkdown }}</pre>
      </div>

      <div class="preview-section">
        <h4>变量检测</h4>
        <div v-if="detectedVariables.length > 0" class="variables-list">
          <div
            v-for="variable in detectedVariables"
            :key="variable"
            class="variable-tag"
            :class="{ declared: isVariableDeclared(variable) }"
          >
            {{ variable }}
            <span v-if="isVariableDeclared(variable)" class="check">✓</span>
            <span v-else class="warning">未声明</span>
          </div>
        </div>
        <div v-else class="empty-variables">
          未检测到变量
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  generatedMarkdown: string
  detectedVariables: string[]
  isVariableDeclared: (variable: string) => boolean
}>()
</script>

<style scoped src="./SkillPreviewPane.css"></style>
