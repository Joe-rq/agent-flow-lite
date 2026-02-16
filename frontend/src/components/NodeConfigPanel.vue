<template>
  <div v-if="visible" class="config-panel">
    <div class="config-header">
      <h3>节点配置</h3>
      <div class="header-actions">
        <button v-if="nodeType" class="help-btn" @click="showHelp = true">查看示例</button>
        <button class="close-btn" @click="handleClose">×</button>
      </div>
    </div>

    <div v-if="nodeId" class="node-id-bar">
      <span class="node-id-label">节点 ID：</span>
      <code class="node-id-value">{{ nodeId }}</code>
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
            :placeholder="hints.start?.inputVariable?.placeholder"
            class="form-input"
          />
          <small class="form-hint">{{ hints.start?.inputVariable?.hint }}</small>
        </div>
      </div>

      <!-- LLM 节点配置 -->
      <LlmNodeConfig
        v-if="nodeType === 'llm'"
        :config="config"
        :skills="skills"
        :models="availableModels"
        @update:config="Object.assign(config, $event)"
        @skill-change="onLLMSkillChange"
      />

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
          <small class="form-hint">{{ hints.knowledge?.knowledgeBaseId?.hint }}</small>
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
            :placeholder="hints.end?.outputVariable?.placeholder"
            class="form-input"
          />
          <small class="form-hint">{{ hints.end?.outputVariable?.hint }}</small>
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
            :placeholder="hints.condition?.expression?.placeholder"
            class="form-textarea"
          ></textarea>
          <small class="form-hint">{{ hints.condition?.expression?.hint }}</small>
        </div>
      </div>

      <!-- Skill 节点配置 -->
      <SkillNodeConfig
        v-if="nodeType === 'skill'"
        :config="config"
        :skills="skills"
        :selected-skill-inputs="selectedSkillInputs"
        :upstream-nodes="upstreamNodes"
        @update:config="Object.assign(config, $event)"
        @skill-change="onSkillChange"
      />

      <!-- HTTP 节点配置 -->
      <div v-if="nodeType === 'http'" class="config-section">
        <h4>HTTP 节点</h4>
        <div class="form-group">
          <label>请求方法</label>
          <select v-model="config.method" class="form-select">
            <option value="GET">GET</option>
            <option value="POST">POST</option>
            <option value="PUT">PUT</option>
            <option value="DELETE">DELETE</option>
          </select>
        </div>
        <div class="form-group">
          <label>URL</label>
          <input v-model="config.url" type="text" class="form-input" :placeholder="hints.http?.url?.placeholder" />
          <small class="form-hint">{{ hints.http?.url?.hint }}</small>
        </div>
        <div class="form-group">
          <label>Headers (JSON)</label>
          <textarea v-model="config.headers" rows="4" class="form-textarea" placeholder='例如：{"Authorization":"Bearer TOKEN"}'></textarea>
        </div>
        <div class="form-group">
          <label>Body (JSON 或文本)</label>
          <textarea v-model="config.body" rows="5" class="form-textarea" placeholder='例如：{"query":"hello"}'></textarea>
        </div>
        <div class="form-group">
          <label>响应提取路径</label>
          <input v-model="config.responsePath" type="text" class="form-input" placeholder="data.result" />
        </div>
        <div class="form-group">
          <label>超时秒数</label>
          <input v-model.number="config.timeoutSeconds" type="number" min="1" max="30" class="form-input" />
        </div>
      </div>

      <!-- Code 节点配置 -->
      <div v-if="nodeType === 'code'" class="config-section">
        <h4>代码节点</h4>
        <div class="form-group">
          <label>Python 代码</label>
          <textarea v-model="config.code" rows="10" class="form-textarea" :placeholder="hints.code?.code?.placeholder"></textarea>
          <small class="form-hint">{{ hints.code?.code?.hint }}</small>
        </div>
        <div class="form-group">
          <label>环境变量 (JSON)</label>
          <textarea v-model="config.env" rows="4" class="form-textarea" placeholder='例如：{"QUERY":"hello"}'></textarea>
        </div>
        <div class="form-group">
          <label>超时秒数</label>
          <input v-model.number="config.timeoutSeconds" type="number" min="1" max="30" class="form-input" />
        </div>
        <div class="form-group">
          <label>内存限制(MB)</label>
          <input v-model.number="config.memoryLimitMb" type="number" min="64" max="512" class="form-input" />
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

    <NodeHelpDialog :visible="showHelp" :node-type="nodeType" @close="showHelp = false" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import LlmNodeConfig from '@/components/config/LlmNodeConfig.vue'
import SkillNodeConfig from '@/components/config/SkillNodeConfig.vue'
import NodeHelpDialog from '@/components/config/NodeHelpDialog.vue'
import { fieldHints as hints } from '@/components/config/nodeHelpData'
import { useNodeConfig, type NodeConfig } from '@/composables/workflow/useNodeConfig'
import type { WorkflowNodeType } from '@/types/workflow'

interface Props {
  visible: boolean
  nodeId: string | null
  nodeType: WorkflowNodeType | null
  nodeData: Record<string, any>
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
  save: [nodeId: string, data: Record<string, any>]
  delete: [nodeId: string]
}>()

const {
  config,
  knowledgeBases,
  skills,
  availableModels,
  upstreamNodes,
  selectedSkillInputs,
  onSkillChange,
  onLLMSkillChange,
} =
  useNodeConfig(props)

const showHelp = ref(false)

const handleClose = () => {
  emit('close')
}

const handleSave = () => {
  if (props.nodeId) {
    const normalized = normalizeConfigForSave(props.nodeType, config.value)
    emit('save', props.nodeId, normalized)
    emit('close')
  } else {
    console.warn('无法保存：nodeId 为空')
  }
}

function parseJsonObject(raw: unknown): Record<string, string> | null {
  if (typeof raw !== 'string' || !raw.trim()) {
    return null
  }
  try {
    const value = JSON.parse(raw)
    if (!value || typeof value !== 'object' || Array.isArray(value)) {
      return null
    }
    const result: Record<string, string> = {}
    for (const [key, item] of Object.entries(value)) {
      result[String(key)] = String(item)
    }
    return result
  } catch {
    return null
  }
}

function normalizeConfigForSave(nodeType: WorkflowNodeType | null, rawConfig: Record<string, unknown>): Record<string, unknown> {
  const normalized: Record<string, unknown> = {}
  const config = rawConfig as NodeConfig

  if (nodeType === 'start') {
    if (config.inputVariable?.trim()) normalized.inputVariable = config.inputVariable.trim()
    return normalized
  }

  if (nodeType === 'llm') {
    if (config.systemPrompt?.trim()) normalized.systemPrompt = config.systemPrompt
    if (typeof config.temperature === 'number') normalized.temperature = config.temperature
    if (config.model?.trim()) normalized.model = config.model.trim()
    if (typeof config.inheritChatHistory === 'boolean') normalized.inheritChatHistory = config.inheritChatHistory
    if (config.skillName?.trim()) normalized.skillName = config.skillName.trim()
    return normalized
  }

  if (nodeType === 'knowledge') {
    if (config.knowledgeBaseId?.trim()) normalized.knowledgeBaseId = config.knowledgeBaseId.trim()
    return normalized
  }

  if (nodeType === 'condition') {
    if (config.expression?.trim()) normalized.expression = config.expression
    return normalized
  }

  if (nodeType === 'skill') {
    if (config.skillName?.trim()) normalized.skillName = config.skillName.trim()
    if (config.inputMappings && typeof config.inputMappings === 'object') normalized.inputMappings = config.inputMappings
    return normalized
  }

  if (nodeType === 'end') {
    if (config.outputVariable?.trim()) normalized.outputVariable = config.outputVariable.trim()
    return normalized
  }

  if (nodeType === 'http') {
    if (config.method) normalized.method = config.method
    if (config.url?.trim()) normalized.url = config.url.trim()
    if (typeof config.timeoutSeconds === 'number') normalized.timeoutSeconds = config.timeoutSeconds
    if (config.responsePath?.trim()) normalized.responsePath = config.responsePath.trim()

    const headers = parseJsonObject(config.headers)
    if (headers) normalized.headers = headers

    if (typeof config.body === 'string' && config.body.trim()) {
      try {
        normalized.body = JSON.parse(config.body)
      } catch {
        normalized.body = config.body
      }
    }

    return normalized
  }

  if (nodeType === 'code') {
    if (config.code?.trim()) normalized.code = config.code
    if (typeof config.timeoutSeconds === 'number') normalized.timeoutSeconds = config.timeoutSeconds
    if (typeof config.memoryLimitMb === 'number') normalized.memoryLimitMb = config.memoryLimitMb

    const env = parseJsonObject(config.env)
    if (env) normalized.env = env

    return normalized
  }

  return normalized
}

const handleDelete = () => {
  if (props.nodeId) {
    emit('delete', props.nodeId)
  }
}
</script>

<style scoped src="./NodeConfigPanel.css"></style>
