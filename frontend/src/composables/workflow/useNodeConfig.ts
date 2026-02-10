import { ref, computed, watch, onMounted } from 'vue'
import axios from 'axios'

export interface NodeConfig {
  inputVariable?: string
  systemPrompt?: string
  temperature?: number
  knowledgeBaseId?: string
  outputVariable?: string
  expression?: string
  skillName?: string
  inputMappings?: Record<string, string>
  skillModelConfig?: { temperature?: number; max_tokens?: number }
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

export interface WorkflowNode {
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

export function useNodeConfig(props: Props) {
  const config = ref<NodeConfig>({
    inputVariable: '',
    systemPrompt: '',
    temperature: 0.7,
    knowledgeBaseId: '',
    outputVariable: '',
    expression: '',
    skillName: '',
    inputMappings: {},
  })

  const knowledgeBases = ref<KnowledgeBase[]>([])
  const skills = ref<Skill[]>([])
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
      knowledgeBaseId: props.nodeData.knowledgeBaseId || '',
      outputVariable: props.nodeData.outputVariable || '',
      expression: props.nodeData.expression || '',
      skillName: props.nodeData.skillName || '',
      inputMappings: props.nodeData.inputMappings || {},
      skillModelConfig: props.nodeData.skillModelConfig || undefined,
    }
  }

  const loadKnowledgeBases = async () => {
    try {
      const response = await axios.get('/api/v1/knowledge/')
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
    upstreamNodes,
    selectedSkillInputs,
    onSkillChange,
    onLLMSkillChange,
  }
}
