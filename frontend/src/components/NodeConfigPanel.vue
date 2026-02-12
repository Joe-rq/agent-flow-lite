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

    <NodeHelpDialog :visible="showHelp" :node-type="nodeType" @close="showHelp = false" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import LlmNodeConfig from '@/components/config/LlmNodeConfig.vue'
import SkillNodeConfig from '@/components/config/SkillNodeConfig.vue'
import NodeHelpDialog from '@/components/config/NodeHelpDialog.vue'
import { fieldHints as hints } from '@/components/config/nodeHelpData'
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

const showHelp = ref(false)

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
