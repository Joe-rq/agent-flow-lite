<template>
  <div class="skill-editor">
    <!-- 头部 -->
    <div class="editor-header">
      <div class="header-left">
        <button class="btn-back" @click="goBack">← 返回列表</button>
        <h1>{{ isNew ? '新建技能' : '编辑技能' }}</h1>
      </div>
      <div class="header-actions">
        <button class="btn-secondary" @click="togglePreview">
          {{ showPreview ? '隐藏预览' : '显示预览' }}
        </button>
        <button
          class="btn-primary"
          :disabled="isSaving || !skillName.trim()"
          @click="saveSkill"
        >
          {{ isSaving ? '保存中...' : '保存' }}
        </button>
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
              <input
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
            <input
              v-model="skillDescription"
              type="text"
              placeholder="简短描述这个技能的功能..."
            />
          </div>

          <!-- 输入参数 -->
          <div class="inputs-section">
            <div class="section-header">
              <label>输入参数</label>
              <button class="btn-add" @click="addInput">+ 添加</button>
            </div>
            <div v-for="(input, index) in skillInputs" :key="index" class="input-row">
              <input
                v-model="input.name"
                type="text"
                placeholder="参数名"
                class="input-name"
              />
              <input
                v-model="input.description"
                type="text"
                placeholder="描述"
                class="input-desc"
              />
              <input
                v-model="input.default"
                type="text"
                placeholder="默认值"
                class="input-default"
              />
              <label class="checkbox-label">
                <input v-model="input.required" type="checkbox" />
                必填
              </label>
              <button class="btn-remove" @click="removeInput(index)">×</button>
            </div>
            <div v-if="skillInputs.length === 0" class="empty-inputs">
              暂无输入参数
            </div>
          </div>
        </div>

        <!-- 提示词编辑 -->
        <div class="prompt-section">
          <label>提示词 (Markdown) <span class="required">*</span></label>
          <textarea
            v-model="skillPrompt"
            class="prompt-textarea"
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
      <div v-if="showPreview" class="preview-pane">
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

// 类型定义
interface SkillInput {
  name: string
  description?: string
  required?: boolean
  default?: string
}

// 路由
const route = useRoute()
const router = useRouter()
const skillNameParam = computed(() => route.params.name as string | undefined)
const isNew = computed(() => !skillNameParam.value || skillNameParam.value === 'new')

// 状态
const skillName = ref('')
const skillDescription = ref('')
const skillInputs = ref<SkillInput[]>([])
const skillPrompt = ref<string>('')
const isSaving = ref(false)
const showPreview = ref(true)
const nameError = ref('')
const promptError = ref('')

const API_BASE = '/api/v1'

// 计算属性：生成的 Markdown
const generatedMarkdown = computed(() => {
  const inputsYaml = skillInputs.value
    .filter(i => i.name.trim())
    .map(i => {
      let line = `  - name: ${i.name.trim()}`
      if (i.description) line += `\n    description: ${i.description}`
      if (i.required) line += '\n    required: true'
      if (i.default) line += `\n    default: ${i.default}`
      return line
    })
    .join('\n')

  let yaml = '---\n'
  yaml += `name: ${skillName.value || 'unnamed'}\n`
  if (skillDescription.value) yaml += `description: ${skillDescription.value}\n`
  if (inputsYaml) yaml += `inputs:\n${inputsYaml}\n`
  yaml += '---\n\n'
  yaml += skillPrompt.value || ''

  return yaml
})

// 计算属性：检测到的变量
const detectedVariables = computed(() => {
  const regex = /\{\{(\w+)\}\}/g
  const matches = new Set<string>()
  let match
  while ((match = regex.exec(skillPrompt.value)) !== null) {
    matches.add(match[1])
  }
  return Array.from(matches)
})

// 检查变量是否已声明
function isVariableDeclared(variable: string): boolean {
  return skillInputs.value.some(input => input.name === variable)
}

// 验证名称
function validateName() {
  nameError.value = ''
  const name = skillName.value.trim()
  if (!name) return

  // 只允许小写字母、数字、连字符
  if (!/^[a-z0-9-]+$/.test(name)) {
    nameError.value = '只能包含小写字母、数字、连字符'
    return
  }
  // 不能以连字符开头或结尾
  if (name.startsWith('-') || name.endsWith('-')) {
    nameError.value = '不能以连字符开头或结尾'
    return
  }
  // 不能有连续连字符
  if (name.includes('--')) {
    nameError.value = '不能有连续连字符'
    return
  }
}

// 添加输入参数
function addInput() {
  skillInputs.value.push({
    name: '',
    description: '',
    required: false,
    default: '',
  })
}

// 移除输入参数
function removeInput(index: number) {
  skillInputs.value.splice(index, 1)
}

// 切换预览
function togglePreview() {
  showPreview.value = !showPreview.value
}

// 返回列表
function goBack() {
  router.push('/skills')
}

// 加载技能
async function loadSkill(name: string) {
  try {
    const response = await axios.get(`${API_BASE}/skills/${name}`)
    const skill = response.data

    skillName.value = skill.name || ''
    skillDescription.value = skill.description || ''
    skillInputs.value = skill.inputs?.map((i: any) => ({
      name: i.name || '',
      description: i.description || '',
      required: i.required || false,
      default: i.default || '',
    })) || []
    skillPrompt.value = skill.prompt || ''
  } catch (error) {
    console.error('加载技能失败:', error)
    alert('加载技能失败')
    router.push('/skills')
  }
}

// 保存技能
async function saveSkill() {
  validateName()
  if (nameError.value) return

  // 验证必填项
  if (!skillName.value.trim()) {
    nameError.value = '请输入技能名称'
    return
  }
  if (!skillPrompt.value.trim()) {
    promptError.value = '请输入提示词内容'
    return
  }

  isSaving.value = true
  promptError.value = ''

  try {
    const payload = {
      name: skillName.value.trim(),
      description: skillDescription.value.trim() || undefined,
      inputs: skillInputs.value
        .filter(i => i.name.trim())
        .map(i => ({
          name: i.name.trim(),
          description: i.description?.trim() || undefined,
          required: i.required || undefined,
          default: i.default?.trim() || undefined,
        })),
      prompt: skillPrompt.value,
      content: generatedMarkdown.value,
    }

    if (isNew.value) {
      await axios.post(`${API_BASE}/skills`, payload)
    } else {
      await axios.put(`${API_BASE}/skills/${skillNameParam.value}`, payload)
    }

    router.push('/skills')
  } catch (error: any) {
    console.error('保存技能失败:', error)
    promptError.value = error.response?.data?.detail || '保存失败，请重试'
  } finally {
    isSaving.value = false
  }
}

// 生命周期
onMounted(() => {
  if (!isNew.value && skillNameParam.value) {
    loadSkill(skillNameParam.value)
  }
})
</script>

<style scoped>
.skill-editor {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 头部 */
.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #e9ecef;
  background: white;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.btn-back {
  background: none;
  border: none;
  color: #3498db;
  cursor: pointer;
  font-size: 14px;
  padding: 0;
}

.btn-back:hover {
  text-decoration: underline;
}

.editor-header h1 {
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.btn-primary {
  background-color: #2c3e50;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background-color: #34495e;
}

.btn-primary:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: #ecf0f1;
  color: #2c3e50;
  border: 1px solid #bdc3c7;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background-color: #d5dbdb;
}

/* 编辑器主体 */
.editor-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 编辑区 */
.editor-pane {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background: #f8f9fa;
}

.editor-pane.expanded {
  flex: 1;
}

/* 元数据表单 */
.metadata-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: #2c3e50;
  font-weight: 500;
}

.form-group label .required {
  color: #e74c3c;
  margin-left: 2px;
}

.form-group input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #bdc3c7;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-group input:focus {
  outline: none;
  border-color: #3498db;
}

.form-group input:disabled {
  background-color: #ecf0f1;
  cursor: not-allowed;
}

.hint {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #7f8c8d;
}

.error-text {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #e74c3c;
}

/* 输入参数 */
.inputs-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e9ecef;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-header label {
  font-size: 14px;
  color: #2c3e50;
  font-weight: 500;
}

.btn-add {
  background-color: #27ae60;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-add:hover {
  background-color: #229954;
}

.input-row {
  display: grid;
  grid-template-columns: 120px 1fr 100px auto 32px;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.input-row input {
  padding: 8px 10px;
  border: 1px solid #bdc3c7;
  border-radius: 4px;
  font-size: 13px;
}

.input-row input:focus {
  outline: none;
  border-color: #3498db;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #2c3e50;
  cursor: pointer;
}

.checkbox-label input {
  margin: 0;
}

.btn-remove {
  width: 28px;
  height: 28px;
  border: none;
  background-color: transparent;
  color: #e74c3c;
  font-size: 18px;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-remove:hover {
  background-color: #ffebee;
}

.empty-inputs {
  text-align: center;
  padding: 20px;
  color: #95a5a6;
  font-size: 13px;
  background: #f8f9fa;
  border-radius: 4px;
}

/* 提示词编辑 */
.prompt-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
}

.prompt-section label {
  display: block;
  margin-bottom: 12px;
  font-size: 14px;
  color: #2c3e50;
  font-weight: 500;
}

.prompt-textarea {
  width: 100%;
  min-height: 400px;
  padding: 12px;
  border: 1px solid #bdc3c7;
  border-radius: 6px;
  font-size: 14px;
  line-height: 1.6;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  resize: vertical;
  box-sizing: border-box;
}

.prompt-textarea:focus {
  outline: none;
  border-color: #3498db;
}

/* 预览区 */
.preview-pane {
  width: 450px;
  border-left: 1px solid #e9ecef;
  background: white;
  display: flex;
  flex-direction: column;
}

.preview-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e9ecef;
}

.preview-header h3 {
  margin: 0;
  font-size: 16px;
  color: #2c3e50;
}

.preview-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.preview-section {
  margin-bottom: 24px;
}

.preview-section h4 {
  margin: 0 0 12px 0;
  font-size: 13px;
  color: #7f8c8d;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.code-block {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.5;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  margin: 0;
}

.variables-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.variable-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  background: #ffebee;
  color: #c62828;
  border: 1px solid #ef9a9a;
}

.variable-tag.declared {
  background: #e8f5e9;
  color: #2e7d32;
  border-color: #a5d6a7;
}

.variable-tag .check {
  font-size: 10px;
}

.variable-tag .warning {
  font-size: 10px;
  opacity: 0.8;
}

.empty-variables {
  color: #95a5a6;
  font-size: 13px;
  font-style: italic;
}
</style>
