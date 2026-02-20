<template>
  <div class="skill-editor">
    <!-- 头部 -->
    <div class="editor-header">
      <div class="header-left">
        <Button class="btn-back" variant="secondary" size="sm" @click="goBack">← 返回列表</Button>
        <h1>{{ isNew ? '新建技能' : '编辑技能' }}</h1>
      </div>
      <div class="header-actions">
        <Button variant="secondary" @click="togglePreview">
          {{ showPreview ? '隐藏预览' : '显示预览' }}
        </Button>
        <Button
          class="btn-primary"
          variant="primary"
          :disabled="isSaving || !skillName.trim()"
          @click="saveSkill"
        >
          {{ isSaving ? '保存中...' : '保存' }}
        </Button>
      </div>
    </div>

    <div class="editor-body">
      <!-- 左侧：编辑区 -->
      <div class="editor-pane" :class="{ expanded: !showPreview }">
        <!-- 元数据表单 -->
        <div class="metadata-section">
          <div class="form-row">
            <div class="form-group">
              <label>技能名称 <span class="required">*</span></label>
              <TextInput
                v-model="skillName"
                type="text"
                placeholder="skill-name"
                :disabled="!isNew"
                @blur="validateName"
              />
              <span v-if="nameError" class="error-text">{{ nameError }}</span>
              <span v-else class="hint">小写字母、数字、连字符，如: text-summarizer</span>
            </div>
          </div>

          <div class="form-group">
            <label>描述</label>
            <TextInput
              v-model="skillDescription"
              type="text"
              placeholder="简短描述这个技能的功能..."
            />
          </div>

          <!-- 输入参数 -->
          <div class="inputs-section">
            <div class="section-header">
              <label>输入参数</label>
              <Button variant="secondary" size="sm" @click="addInput">+ 添加</Button>
            </div>
            <div v-for="(input, index) in skillInputs" :key="index" class="input-row">
              <TextInput
                v-model="input.name"
                type="text"
                placeholder="参数名"
              />
              <TextInput
                v-model="input.description"
                type="text"
                placeholder="描述"
              />
              <TextInput
                v-model="input.default"
                type="text"
                placeholder="默认值"
              />
              <label class="checkbox-label">
                <input v-model="input.required" type="checkbox" />
                必填
              </label>
              <Button class="btn-remove" variant="danger" size="sm" @click="removeInput(index)">×</Button>
            </div>
            <div v-if="skillInputs.length === 0" class="empty-inputs">
              暂无输入参数
            </div>
          </div>
        </div>

        <!-- 提示词编辑 -->
        <div class="prompt-section">
          <label>提示词 (Markdown) <span class="required">*</span></label>
          <TextArea
            v-model="skillPrompt"
            placeholder="# 提示词内容

使用 {{variable}} 语法引用输入参数...

例如:
请总结以下文本:
{{text}}

要求:
- 长度不超过 {{max_length}} 字"
          />
          <span v-if="promptError" class="error-text">{{ promptError }}</span>
        </div>
      </div>

      <!-- 右侧：预览区 -->
      <SkillPreviewPane
        v-if="showPreview"
        :generatedMarkdown="generatedMarkdown"
        :detectedVariables="detectedVariables"
        :isVariableDeclared="isVariableDeclared"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useSkillForm } from '@/composables/skills/useSkillForm'
import { Button, TextInput, TextArea } from '@/components/ui'
import SkillPreviewPane from '@/components/skills/SkillPreviewPane.vue'

const {
  isNew,
  skillNameParam,
  skillName,
  skillDescription,
  skillInputs,
  skillPrompt,
  isSaving,
  showPreview,
  nameError,
  promptError,
  generatedMarkdown,
  detectedVariables,
  isVariableDeclared,
  validateName,
  addInput,
  removeInput,
  togglePreview,
  goBack,
  loadSkill,
  saveSkill,
} = useSkillForm()

onMounted(() => {
  if (!isNew.value && skillNameParam.value) {
    loadSkill(skillNameParam.value)
  }
})
</script>

<style scoped src="./SkillEditor.css"></style>
