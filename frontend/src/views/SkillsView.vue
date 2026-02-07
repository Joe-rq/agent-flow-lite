<template>
  <div class="skills-view">
    <div class="page-header">
      <h1>技能管理</h1>
      <button class="btn-primary" @click="createNewSkill">
        + 新建技能
      </button>
    </div>

    <!-- 技能列表 -->
    <div class="skills-list">
      <div
        v-for="skill in skills"
        :key="skill.name"
        class="skill-card"
        @click="editSkill(skill.name)"
      >
        <div class="skill-card-header">
          <h3 class="skill-name">{{ skill.name }}</h3>
        </div>
        <p class="skill-description">{{ skill.description || '暂无描述' }}</p>
        <div class="skill-inputs" v-if="skill.inputs && skill.inputs.length > 0">
          <span class="inputs-label">输入参数:</span>
          <span
            v-for="input in skill.inputs.slice(0, 3)"
            :key="input.name"
            class="input-tag"
            :class="{ required: input.required }"
          >
            {{ input.name }}
          </span>
          <span v-if="skill.inputs.length > 3" class="input-tag more">
            +{{ skill.inputs.length - 3 }}
          </span>
        </div>
        <div class="skill-card-footer">
          <span class="skill-updated">更新于 {{ formatDate(skill.updatedAt) }}</span>
          <div class="skill-actions">
            <button
              class="btn-run"
              @click.stop="openRunModal(skill)"
            >
              运行
            </button>
            <button
              class="btn-delete-skill"
              @click.stop="deleteSkill(skill.name)"
            >
              删除
            </button>
          </div>
        </div>
      </div>

      <div v-if="skills.length === 0" class="empty-state">
        <p>暂无技能</p>
        <button class="btn-primary" @click="createNewSkill">
          创建第一个技能
        </button>
      </div>
    </div>

    <!-- 运行技能对话框 -->
    <div v-if="showRunModal" class="dialog-overlay" @click.self="closeRunModal">
      <div class="dialog run-dialog">
        <div class="dialog-header">
          <h3>运行技能: {{ runningSkill?.name }}</h3>
          <button class="btn-close" @click="closeRunModal">×</button>
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
            @click="closeRunModal"
            :disabled="isRunning"
          >
            取消
          </button>
          <button
            class="btn-primary"
            :disabled="isRunning"
            @click="runSkill"
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
          <div class="output-content" ref="outputContainer">
            <div v-if="currentThought" class="thought-line">
              <span class="thought-icon">💭</span>
              <span class="thought-text">{{ currentThought }}</span>
            </div>
            <div class="output-text">{{ runOutput }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

// 类型定义
interface SkillInput {
  name: string
  description?: string
  required?: boolean
  default?: string
}

interface Skill {
  name: string
  description?: string
  inputs: SkillInput[]
  updatedAt: string
}

interface SkillApiItem {
  name: string
  description?: string
  inputs?: SkillInput[]
  updated_at?: string
  updatedAt?: string
}

// 状态
const router = useRouter()
const skills = ref<Skill[]>([])
const showRunModal = ref(false)
const runningSkill = ref<Skill | null>(null)
const runInputs = ref<Record<string, string>>({})
const runOutput = ref('')
const isRunning = ref(false)
const currentThought = ref('')
const outputContainer = ref<HTMLElement | null>(null)

const API_BASE = '/api/v1'
const authStore = useAuthStore()

// 格式化日期
function formatDate(dateStr: string): string {
  if (!dateStr) return '未知'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 加载技能列表
async function loadSkills() {
  try {
    const response = await axios.get(`${API_BASE}/skills`)
    const rawSkills: SkillApiItem[] = Array.isArray(response?.data)
      ? response.data
      : response?.data?.skills || response?.data?.items || []

    skills.value = rawSkills.map(skill => ({
      name: skill.name,
      description: skill.description,
      inputs: skill.inputs || [],
      updatedAt: skill.updated_at || skill.updatedAt || '',
    }))
  } catch (error) {
    console.error('加载技能列表失败:', error)
    alert('加载技能列表失败')
  }
}

// 创建新技能
function createNewSkill() {
  router.push('/skills/new')
}

// 编辑技能
function editSkill(name: string) {
  router.push(`/skills/${name}`)
}

// 删除技能
async function deleteSkill(name: string) {
  if (!confirm(`确定要删除技能「${name}」吗？`)) return

  try {
    await axios.delete(`${API_BASE}/skills/${name}`)
    skills.value = skills.value.filter(s => s.name !== name)
  } catch (error: any) {
    console.error('删除技能失败:', error)
    alert(error.response?.data?.detail || '删除技能失败')
  }
}

// 打开运行对话框
function openRunModal(skill: Skill) {
  runningSkill.value = skill
  runInputs.value = {}
  runOutput.value = ''
  currentThought.value = ''
  isRunning.value = false

  // 设置默认值
  skill.inputs?.forEach(input => {
    if (input.default) {
      runInputs.value[input.name] = input.default
    }
  })

  showRunModal.value = true
}

// 关闭运行对话框
function closeRunModal() {
  if (isRunning.value) return
  showRunModal.value = false
  runningSkill.value = null
  runInputs.value = {}
  runOutput.value = ''
  currentThought.value = ''
}

// 滚动输出到底部
function scrollOutputToBottom() {
  nextTick(() => {
    if (outputContainer.value) {
      outputContainer.value.scrollTop = outputContainer.value.scrollHeight
    }
  })
}

// 运行技能
async function runSkill() {
  if (!runningSkill.value || isRunning.value) return

  // 验证必填项
  const missingInputs = runningSkill.value.inputs?.filter(
    input => input.required && !runInputs.value[input.name]?.trim()
  )
  if (missingInputs?.length) {
    alert(`请填写必填项: ${missingInputs.map(i => i.name).join(', ')}`)
    return
  }

  isRunning.value = true
  runOutput.value = ''
  currentThought.value = ''

  try {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    if (authStore.token) {
      headers['Authorization'] = `Bearer ${authStore.token}`
    }

    const response = await fetch(`${API_BASE}/skills/${runningSkill.value.name}/run`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ inputs: runInputs.value }),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()

    if (!reader) {
      throw new Error('No response body')
    }

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      const lines = chunk.split('\n')

      let currentEvent = ''
      for (const line of lines) {
        if (line.startsWith('event: ')) {
          currentEvent = line.slice(7).trim()
        } else if (line.startsWith('data: ')) {
          const dataStr = line.slice(6)
          if (dataStr === '[DONE]') {
            isRunning.value = false
            currentThought.value = ''
            return
          }

          try {
            const data = JSON.parse(dataStr)
            handleSSEEvent(currentEvent, data)
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }
  } catch (error: any) {
    console.error('运行技能失败:', error)
    runOutput.value += '\n[错误: ' + (error.message || '运行失败') + ']'
  } finally {
    isRunning.value = false
    currentThought.value = ''
  }
}

// 处理 SSE 事件
function handleSSEEvent(eventType: string, data: any) {
  switch (eventType) {
    case 'thought':
      currentThought.value = data.message || data.status || ''
      scrollOutputToBottom()
      break
    case 'token':
      runOutput.value += data.content || ''
      scrollOutputToBottom()
      break
    case 'citation':
      // 引用信息，可以显示在输出中
      if (data.sources && data.sources.length > 0) {
        runOutput.value += '\n[引用 ' + data.sources.length + ' 个来源]'
        scrollOutputToBottom()
      }
      break
    case 'done':
      isRunning.value = false
      currentThought.value = ''
      break
    case 'error':
      runOutput.value += '\n[错误: ' + (data.content || data.message || '未知错误') + ']'
      isRunning.value = false
      currentThought.value = ''
      scrollOutputToBottom()
      break
  }
}

// 生命周期
onMounted(() => {
  loadSkills()
})
</script>

<style scoped>
.skills-view {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
}

/* 按钮样式 */
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

.btn-secondary:hover:not(:disabled) {
  background-color: #d5dbdb;
}

.btn-secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 技能列表 */
.skills-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.skill-card {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
}

.skill-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #3498db;
}

.skill-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.skill-name {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
}

.skill-description {
  color: #7f8c8d;
  font-size: 14px;
  line-height: 1.5;
  margin: 0 0 16px 0;
  flex: 1;
}

.skill-inputs {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-bottom: 16px;
}

.inputs-label {
  font-size: 12px;
  color: #95a5a6;
  margin-right: 4px;
}

.input-tag {
  background-color: #f5f5f5;
  color: #666;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  border: 1px solid #e0e0e0;
}

.input-tag.required {
  background-color: #fff3e0;
  color: #e65100;
  border-color: #ffcc80;
}

.input-tag.more {
  background-color: #e0e0e0;
  color: #666;
}

.skill-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #e9ecef;
}

.skill-updated {
  color: #95a5a6;
  font-size: 12px;
}

.skill-actions {
  display: flex;
  gap: 8px;
}

.btn-run {
  background-color: #27ae60;
  color: white;
  border: none;
  padding: 6px 14px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-run:hover {
  background-color: #229954;
}

.btn-delete-skill {
  padding: 6px 12px;
  background-color: transparent;
  color: #e74c3c;
  border: 1px solid #e74c3c;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  opacity: 0;
}

.skill-card:hover .btn-delete-skill {
  opacity: 1;
}

.btn-delete-skill:hover {
  background-color: #e74c3c;
  color: white;
}

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 60px 20px;
  color: #7f8c8d;
}

.empty-state p {
  margin-bottom: 20px;
  font-size: 16px;
}

/* 对话框 */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: white;
  border-radius: 8px;
  padding: 24px;
  width: 500px;
  max-width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
}

.run-dialog {
  width: 600px;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.dialog-header h3 {
  margin: 0;
  font-size: 18px;
  color: #2c3e50;
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  color: #95a5a6;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.btn-close:hover {
  background-color: #f5f5f5;
  color: #e74c3c;
}

/* 运行输入 */
.run-inputs {
  margin-bottom: 20px;
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

.required-mark {
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

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-bottom: 20px;
}

/* 运行输出 */
.run-output {
  border: 1px solid #e9ecef;
  border-radius: 6px;
  background-color: #f8f9fa;
}

.output-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e9ecef;
  font-size: 13px;
  font-weight: 500;
  color: #2c3e50;
}

.running-indicator {
  display: flex;
  gap: 3px;
}

.running-indicator .dot {
  width: 5px;
  height: 5px;
  background-color: #3498db;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.running-indicator .dot:nth-child(2) {
  animation-delay: 0.2s;
}

.running-indicator .dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-3px);
  }
}

.output-content {
  padding: 16px;
  max-height: 300px;
  overflow-y: auto;
  font-size: 14px;
  line-height: 1.6;
  color: #2c3e50;
  white-space: pre-wrap;
  word-break: break-word;
}

.thought-line {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding: 8px 12px;
  background-color: #f3e5f5;
  border-radius: 6px;
}

.thought-icon {
  font-size: 14px;
}

.thought-text {
  font-size: 13px;
  color: #7b1fa2;
}

.output-text {
  min-height: 20px;
}
</style>
