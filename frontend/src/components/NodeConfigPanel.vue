<template>
  <div v-if="visible" class="config-panel">
    <div class="config-header">
      <h3>节点配置</h3>
      <button class="close-btn" @click="handleClose">×</button>
    </div>

    <div class="config-body">
      <!-- Start 节点配置 -->
      <div v-if="nodeType === 'start'" class="config-section">
        <h4>开始节点</h4>
        <div class="form-group">
          <label>输入变量定义</label>
          <input
            v-model="config.inputVariable"
            type="text"
            placeholder="例如: user_query"
            class="form-input"
          />
        </div>
      </div>

      <!-- LLM 节点配置 -->
      <div v-if="nodeType === 'llm'" class="config-section">
        <h4>LLM 节点</h4>

        <!-- 技能选择 -->
        <div class="form-group">
          <label>加载技能 (可选)</label>
          <select v-model="config.skillName" class="form-select" @change="onLLMSkillChange">
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
            v-model="config.systemPrompt"
            rows="6"
            placeholder="输入系统提示词..."
            class="form-textarea"
            :disabled="!!config.skillName"
          ></textarea>
          <small v-if="config.skillName" class="form-hint">提示词由技能提供，不可编辑</small>
        </div>

        <!-- 温度参数 -->
        <div class="form-group">
          <label>温度参数: {{ config.temperature }}</label>
          <input
            v-model.number="config.temperature"
            type="range"
            min="0"
            max="1"
            step="0.1"
            class="form-range"
            :disabled="!!config.skillName"
          />
          <div class="range-labels">
            <span>精确</span>
            <span>创意</span>
          </div>
          <small v-if="config.skillName" class="form-hint">温度参数由技能配置提供</small>
        </div>
      </div>

      <!-- Knowledge 节点配置 -->
      <div v-if="nodeType === 'knowledge'" class="config-section">
        <h4>知识库节点</h4>
        <div class="form-group">
          <label>选择知识库</label>
          <select v-model="config.knowledgeBaseId" class="form-select">
            <option value="">请选择知识库</option>
            <option v-for="kb in knowledgeBases" :key="kb.id" :value="kb.id">
              {{ kb.name }}
            </option>
          </select>
        </div>
      </div>

      <!-- End 节点配置 -->
      <div v-if="nodeType === 'end'" class="config-section">
        <h4>结束节点</h4>
        <div class="form-group">
          <label>输出变量</label>
          <input
            v-model="config.outputVariable"
            type="text"
            placeholder="例如: result"
            class="form-input"
          />
        </div>
      </div>

      <!-- Condition 节点配置 -->
      <div v-if="nodeType === 'condition'" class="config-section">
        <h4>条件节点</h4>
        <div class="form-group">
          <label>条件表达式 (JavaScript)</label>
          <textarea
            v-model="config.expression"
            rows="4"
            placeholder="例如: {{step1.output}} === 'yes'"
            class="form-textarea"
          ></textarea>
          <small class="form-hint">使用 &#123;&#123;stepId.output&#125;&#125; 引用其他节点的输出</small>
        </div>
      </div>

      <!-- Skill 节点配置 -->
      <div v-if="nodeType === 'skill'" class="config-section">
        <h4>技能节点</h4>
        <div class="form-group">
          <label>选择技能</label>
          <select v-model="config.skillName" class="form-select" @change="onSkillChange">
            <option value="">请选择技能</option>
            <option v-for="skill in skills" :key="skill.name" :value="skill.name">
              {{ skill.name }}
            </option>
          </select>
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

      <!-- 未知节点类型 -->
      <div v-if="!nodeType" class="config-section">
        <p class="empty-text">请选择节点进行配置</p>
      </div>
    </div>

    <div class="config-footer">
      <button class="save-btn" @click="handleSave">保存</button>
      <button class="delete-btn" @click="handleDelete">删除节点</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import axios from 'axios'

interface KnowledgeBase {
  id: string
  name: string
}

interface NodeConfig {
  inputVariable?: string
  systemPrompt?: string
  temperature?: number
  knowledgeBaseId?: string
  outputVariable?: string
  expression?: string
  skillName?: string
  inputMappings?: Record<string, string>
  skillModelConfig?: {
    temperature?: number
    max_tokens?: number
  }
}

interface Skill {
  name: string
  description?: string
  inputs?: Array<{ name: string; label?: string; required?: boolean }>
}

interface WorkflowNode {
  id: string
  label?: string
  type?: string
}

interface Props {
  visible: boolean
  nodeId: string | null
  nodeType: string | null
  nodeData: Record<string, any>
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
  save: [nodeId: string, data: Record<string, any>]
  delete: [nodeId: string]
}>()

// 本地配置状态
const config = ref<NodeConfig>({
  inputVariable: '',
  systemPrompt: '',
  temperature: 0.7,
  knowledgeBaseId: '',
  outputVariable: '',
  expression: '',
  skillName: '',
  inputMappings: {}
})

// 知识库列表
const knowledgeBases = ref<KnowledgeBase[]>([])

// 技能列表
const skills = ref<Skill[]>([])

// 上游节点列表
const upstreamNodes = ref<WorkflowNode[]>([])

// 加载知识库列表
const loadKnowledgeBases = async () => {
  try {
    // 调用后端 API 获取知识库列表
    const response = await axios.get('/api/v1/knowledge/')
    // 适配后端返回格式 { items: [...], total: number }
    let kbList = []
    if (response.data && Array.isArray(response.data.items)) {
      kbList = response.data.items
    } else if (Array.isArray(response.data)) {
      kbList = response.data
    }
    knowledgeBases.value = kbList.map((kb: any) => ({
      id: kb.id || kb.kb_id,
      name: kb.name || kb.kb_name || '未命名知识库'
    }))
  } catch (error) {
    console.error('加载知识库列表失败:', error)
    knowledgeBases.value = []
  }
}

// 从节点数据同步配置
const syncFromNodeData = () => {
  if (props.nodeData) {
    config.value = {
      inputVariable: props.nodeData.inputVariable || '',
      systemPrompt: props.nodeData.systemPrompt || '',
      temperature: props.nodeData.temperature ?? 0.7,
      knowledgeBaseId: props.nodeData.knowledgeBaseId || '',
      outputVariable: props.nodeData.outputVariable || '',
      expression: props.nodeData.expression || '',
      skillName: props.nodeData.skillName || '',
      inputMappings: props.nodeData.inputMappings || {},
      skillModelConfig: props.nodeData.skillModelConfig || undefined
    }
  }
}

// 监听节点数据变化
watch(() => props.nodeData, syncFromNodeData, { immediate: true, deep: true })

// 监听节点类型变化，加载知识库或技能
watch(() => props.nodeType, (newType) => {
  if (newType === 'knowledge') {
    loadKnowledgeBases()
  } else if (newType === 'skill' || newType === 'llm') {
    loadSkills()
    if (newType === 'skill') {
      loadUpstreamNodes()
    }
  }
})

// 监听 visible 变化，当面板打开时同步数据
watch(() => props.visible, (isVisible) => {
  if (isVisible) {
    syncFromNodeData()
    if (props.nodeType === 'knowledge') {
      loadKnowledgeBases()
    } else if (props.nodeType === 'skill' || props.nodeType === 'llm') {
      loadSkills()
      if (props.nodeType === 'skill') {
        loadUpstreamNodes()
      }
    }
  }
})

// 计算选中的技能的输入列表
const selectedSkillInputs = computed(() => {
  const skill = skills.value.find(s => s.name === config.value.skillName)
  return skill?.inputs || []
})

// 加载技能列表
const loadSkills = async () => {
  try {
    const response = await axios.get('/api/v1/skills')
    skills.value = response.data.skills || []
  } catch (error) {
    console.error('加载技能列表失败:', error)
    skills.value = []
  }
}

// 加载上游节点
const loadUpstreamNodes = () => {
  // Get upstream nodes from parent component via custom event
  // For now, we'll use a simple approach - the parent will pass this via nodeData
  upstreamNodes.value = []
}

// 技能选择变化
const onSkillChange = () => {
  // Reset input mappings when skill changes
  config.value.inputMappings = {}
}

// LLM节点技能选择变化
const onLLMSkillChange = async () => {
  const skillName = config.value.skillName
  if (!skillName) {
    // 清除技能时，恢复默认值
    config.value.systemPrompt = ''
    config.value.temperature = 0.7
    config.value.skillModelConfig = undefined
    return
  }

  // 加载技能详情以获取提示词和模型配置
  try {
    const response = await axios.get(`/api/v1/skills/${skillName}`)
    const skill = response.data

    // 更新提示词
    if (skill.prompt) {
      config.value.systemPrompt = skill.prompt
    }

    // 更新模型配置
    if (skill.model) {
      config.value.temperature = skill.model.temperature ?? 0.7
      config.value.skillModelConfig = {
        temperature: skill.model.temperature ?? 0.7,
        max_tokens: skill.model.max_tokens ?? 2000
      }
    }
  } catch (error) {
    console.error('加载技能详情失败:', error)
  }
}

// 关闭面板
const handleClose = () => {
  emit('close')
}

// 保存配置
const handleSave = () => {
  if (props.nodeId) {
    emit('save', props.nodeId, { ...config.value })
    emit('close')
  } else {
    console.warn('无法保存：nodeId 为空')
  }
}

// 删除节点
const handleDelete = () => {
  if (props.nodeId) {
    emit('delete', props.nodeId)
  }
}

onMounted(() => {
  if (props.nodeType === 'knowledge') {
    loadKnowledgeBases()
  } else if (props.nodeType === 'skill' || props.nodeType === 'llm') {
    loadSkills()
    if (props.nodeType === 'skill') {
      loadUpstreamNodes()
    }
  }
})
</script>

<style scoped>
.config-panel {
  position: fixed;
  right: 0;
  top: 60px;
  bottom: 0;
  width: 360px;
  background: #ffffff;
  border-left: 1px solid #e5e7eb;
  box-shadow: -4px 0 6px -1px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  z-index: 100;
}

.config-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.config-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.close-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  color: #6b7280;
  font-size: 20px;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #e5e7eb;
  color: #374151;
}

.config-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.config-section h4 {
  margin: 0 0 16px 0;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

.form-input,
.form-textarea,
.form-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  color: #111827;
  background: #ffffff;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-input:focus,
.form-textarea:focus,
.form-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-textarea {
  resize: vertical;
  min-height: 120px;
  font-family: inherit;
}

.form-select {
  cursor: pointer;
}

.form-range {
  width: 100%;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: #e5e7eb;
  border-radius: 3px;
  outline: none;
  margin: 10px 0;
}

.form-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  background: #3b82f6;
  border-radius: 50%;
  cursor: pointer;
  transition: background 0.2s;
}

.form-range::-webkit-slider-thumb:hover {
  background: #2563eb;
}

.form-range::-moz-range-thumb {
  width: 18px;
  height: 18px;
  background: #3b82f6;
  border-radius: 50%;
  cursor: pointer;
  border: none;
  transition: background 0.2s;
}

.form-range::-moz-range-thumb:hover {
  background: #2563eb;
}

.range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #6b7280;
}

.empty-text {
  text-align: center;
  color: #6b7280;
  font-size: 14px;
  padding: 40px 0;
}

.config-footer {
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
}

.save-btn {
  width: 100%;
  padding: 10px 16px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.save-btn:hover {
  background: #2563eb;
}

.save-btn:active {
  background: #1d4ed8;
}

.delete-btn {
  width: 100%;
  padding: 10px 16px;
  background: #ffffff;
  color: #dc2626;
  border: 1px solid #fca5a5;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 8px;
}

.delete-btn:hover {
  background: #fef2f2;
  border-color: #dc2626;
}

.delete-btn:active {
  background: #fee2e2;
}

.form-hint {
  display: block;
  margin-top: 6px;
  font-size: 12px;
  color: #6b7280;
}

.input-mapping-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.input-name {
  min-width: 80px;
  font-size: 13px;
  color: #374151;
  font-weight: 500;
}

.mapping-select {
  flex: 1;
}
</style>
