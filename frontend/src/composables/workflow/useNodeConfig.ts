import { ref, computed, watch, onMounted } from 'vue'
import axios from 'axios'

import type { WorkflowNodeType } from '@/types/workflow'

export interface NodeConfig {
  inputVariable?: string
  systemPrompt?: string
  temperature?: number
  model?: string
  inheritChatHistory?: boolean
  knowledgeBaseId?: string
  outputVariable?: string
  expression?: string
  skillName?: string
  inputMappings?: Record<string, string>
  skillModelConfig?: { temperature?: number; max_tokens?: number }
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  url?: string
  headers?: string
  body?: string
  responsePath?: string
  timeoutSeconds?: number
  code?: string
  memoryLimitMb?: number
  env?: string
}

export interface KnowledgeBase {
  id: string
  name: string
}

export interface Skill {
  name: string
  description?: string
  inputs?: Array<{ name: string; label?: string; required?: boolean }>
}

export interface AvailableModel {
  id: string
  provider: string
  model: string
}

export interface WorkflowNode {
  id: string
  label?: string
  type?: string
}

interface Props {
  visible: boolean
  nodeId: string | null
  nodeType: WorkflowNodeType | null
  nodeData: Record<string, any>
}

export function useNodeConfig(props: Props) {
  const config = ref<NodeConfig>({
    inputVariable: '',
    systemPrompt: '',
    temperature: 0.7,
    model: '',
    inheritChatHistory: false,
    knowledgeBaseId: '',
    outputVariable: '',
    expression: '',
    skillName: '',
    inputMappings: {},
    method: 'GET',
    url: '',
    headers: '',
    body: '',
    responsePath: '',
    timeoutSeconds: 10,
    code: '',
    memoryLimitMb: 256,
    env: '',
  })

  const knowledgeBases = ref<KnowledgeBase[]>([])
  const skills = ref<Skill[]>([])
  const availableModels = ref<AvailableModel[]>([])
  const defaultModel = ref('')
  const upstreamNodes = ref<WorkflowNode[]>([])

  const selectedSkillInputs = computed(() => {
    const skill = skills.value.find((s) => s.name === config.value.skillName)
    return skill?.inputs || []
  })

  const syncFromNodeData = () => {
    if (!props.nodeData) return
    config.value = {
      inputVariable: props.nodeData.inputVariable || '',
      systemPrompt: props.nodeData.systemPrompt || '',
      temperature: props.nodeData.temperature ?? 0.7,
      model: props.nodeData.model || '',
      inheritChatHistory: !!props.nodeData.inheritChatHistory,
      knowledgeBaseId: props.nodeData.knowledgeBaseId || '',
      outputVariable: props.nodeData.outputVariable || '',
      expression: props.nodeData.expression || '',
      skillName: props.nodeData.skillName || '',
      inputMappings: props.nodeData.inputMappings || {},
      skillModelConfig: props.nodeData.skillModelConfig || undefined,
      method: props.nodeData.method || 'GET',
      url: props.nodeData.url || '',
      headers: props.nodeData.headers ? JSON.stringify(props.nodeData.headers, null, 2) : '',
      body:
        typeof props.nodeData.body === 'string'
          ? props.nodeData.body
          : props.nodeData.body
            ? JSON.stringify(props.nodeData.body, null, 2)
            : '',
      responsePath: props.nodeData.responsePath || '',
      timeoutSeconds: props.nodeData.timeoutSeconds ?? 10,
      code: props.nodeData.code || '',
      memoryLimitMb: props.nodeData.memoryLimitMb ?? 256,
      env: props.nodeData.env ? JSON.stringify(props.nodeData.env, null, 2) : '',
    }
  }

  const loadModels = async () => {
    try {
      const response = await axios.get('/api/v1/chat/models')
      const items = Array.isArray(response.data?.items) ? response.data.items : []
      availableModels.value = items.map((item: any) => ({
        id: item.id,
        provider: item.provider,
        model: item.model,
      }))
      defaultModel.value = response.data?.default_model || ''
      if (!config.value.model && defaultModel.value) {
        config.value.model = defaultModel.value
      }
    } catch (error) {
      console.error('加载模型列表失败:', error)
      availableModels.value = []
      defaultModel.value = ''
    }
  }

  const loadKnowledgeBases = async () => {
    try {
      const response = await axios.get('/api/v1/knowledge')
      let kbList = []
      if (response.data && Array.isArray(response.data.items)) {
        kbList = response.data.items
      } else if (Array.isArray(response.data)) {
        kbList = response.data
      }
      knowledgeBases.value = kbList.map((kb: any) => ({
        id: kb.id || kb.kb_id,
        name: kb.name || kb.kb_name || '未命名知识库',
      }))
    } catch (error) {
      console.error('加载知识库列表失败:', error)
      knowledgeBases.value = []
    }
  }

  const loadSkills = async () => {
    try {
      const response = await axios.get('/api/v1/skills')
      skills.value = response.data.skills || []
    } catch (error) {
      console.error('加载技能列表失败:', error)
      skills.value = []
    }
  }

  const loadUpstreamNodes = () => {
    upstreamNodes.value = []
  }

  const onSkillChange = () => {
    config.value.inputMappings = {}
  }

  const onLLMSkillChange = async () => {
    const skillName = config.value.skillName
    if (!skillName) {
      config.value.systemPrompt = ''
      config.value.temperature = 0.7
      config.value.skillModelConfig = undefined
      return
    }
    try {
      const response = await axios.get(`/api/v1/skills/${skillName}`)
      const skill = response.data
      if (skill.prompt) {
        config.value.systemPrompt = skill.prompt
      }
      if (skill.model) {
        config.value.temperature = skill.model.temperature ?? 0.7
        config.value.skillModelConfig = {
          temperature: skill.model.temperature ?? 0.7,
          max_tokens: skill.model.max_tokens ?? 2000,
        }
      }
    } catch (error) {
      console.error('加载技能详情失败:', error)
    }
  }

  const loadByNodeType = (nodeType: string | null) => {
    if (nodeType === 'knowledge') {
      loadKnowledgeBases()
    } else if (nodeType === 'skill' || nodeType === 'llm') {
      loadSkills()
      if (nodeType === 'llm') loadModels()
      if (nodeType === 'skill') loadUpstreamNodes()
    }
  }

  watch(() => props.nodeData, syncFromNodeData, { immediate: true, deep: true })

  watch(
    () => props.nodeType,
    (newType) => loadByNodeType(newType),
  )

  watch(
    () => props.visible,
    (isVisible) => {
      if (isVisible) {
        syncFromNodeData()
        loadByNodeType(props.nodeType)
      }
    },
  )

  onMounted(() => loadByNodeType(props.nodeType))

  return {
    config,
    knowledgeBases,
    skills,
    availableModels,
    defaultModel,
    upstreamNodes,
    selectedSkillInputs,
    onSkillChange,
    onLLMSkillChange,
  }
}
