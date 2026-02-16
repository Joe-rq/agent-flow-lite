export type WorkflowNodeType =
  | 'start'
  | 'llm'
  | 'knowledge'
  | 'condition'
  | 'skill'
  | 'http'
  | 'code'
  | 'end'

export interface StartNodeData {
  inputVariable?: string
}

export interface LlmNodeData {
  systemPrompt?: string
  temperature?: number
  model?: string
  inheritChatHistory?: boolean
  skillName?: string
}

export interface KnowledgeNodeData {
  knowledgeBaseId?: string
}

export interface ConditionNodeData {
  expression?: string
}

export interface SkillNodeData {
  skillName?: string
  inputMappings?: Record<string, string>
}

export interface HttpNodeData {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  url?: string
  headers?: Record<string, string>
  body?: Record<string, string> | string
  responsePath?: string
  timeoutSeconds?: number
}

export interface CodeNodeData {
  code?: string
  env?: Record<string, string>
  timeoutSeconds?: number
  memoryLimitMb?: number
}

export interface EndNodeData {
  outputVariable?: string
}

export interface WorkflowNodeDataMap {
  start: StartNodeData
  llm: LlmNodeData
  knowledge: KnowledgeNodeData
  condition: ConditionNodeData
  skill: SkillNodeData
  http: HttpNodeData
  code: CodeNodeData
  end: EndNodeData
}

export type WorkflowNodeData = WorkflowNodeDataMap[WorkflowNodeType]

export type WorkflowNode<T extends WorkflowNodeType = WorkflowNodeType> = {
  id: string
  type: T
  data: WorkflowNodeDataMap[T]
  [key: string]: unknown
}

export type WorkflowEdge = Record<string, unknown>

export interface WorkflowGraphData {
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
}
