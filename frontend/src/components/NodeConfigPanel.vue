<template>
  <div v-if="visible" class="config-panel">
    <div class="config-header">
      <h3>节点配置</h3>
      <button class="close-btn" @click="handleClose">×</button>
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
            placeholder="例如: user_query"
            class="form-input"
          />
        </div>
      </div>

      <!-- LLM 节点配置 -->
      <LlmNodeConfig
        v-if="nodeType === 'llm'"
        :config="config"
        :skills="skills"
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
      <SkillNodeConfig
        v-if="nodeType === 'skill'"
        :config="config"
        :skills="skills"
        :selected-skill-inputs="selectedSkillInputs"
        :upstream-nodes="upstreamNodes"
        @skill-change="onSkillChange"
      />

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
import LlmNodeConfig from '@/components/config/LlmNodeConfig.vue'
import SkillNodeConfig from '@/components/config/SkillNodeConfig.vue'
import { useNodeConfig } from '@/composables/workflow/useNodeConfig'

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

const { config, knowledgeBases, skills, upstreamNodes, selectedSkillInputs, onSkillChange, onLLMSkillChange } =
  useNodeConfig(props)

const handleClose = () => {
  emit('close')
}

const handleSave = () => {
  if (props.nodeId) {
    emit('save', props.nodeId, { ...config.value })
    emit('close')
  } else {
    console.warn('无法保存：nodeId 为空')
  }
}

const handleDelete = () => {
  if (props.nodeId) {
    emit('delete', props.nodeId)
  }
}
</script>

<style scoped src="./NodeConfigPanel.css"></style>
