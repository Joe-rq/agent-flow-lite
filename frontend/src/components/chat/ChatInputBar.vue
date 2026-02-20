<template>
  <div class="chat-input-wrapper">
    <!-- 配置栏：单行紧凑 -->
    <div class="input-config-bar">
      <div class="config-selects">
        <div class="config-select-item">
          <label>工作流</label>
          <select
            :value="selectedWorkflowId"
            :disabled="isStreaming"
            @change="$emit('update:selectedWorkflowId', ($event.target as HTMLSelectElement).value)"
          >
            <option value="">无</option>
            <option v-for="wf in workflows" :key="wf.id" :value="wf.id">
              {{ wf.name }}
            </option>
          </select>
        </div>
        <div class="config-select-item">
          <label>知识库</label>
          <select
            :value="selectedKbId"
            :disabled="isStreaming || !!selectedWorkflowId"
            @change="$emit('update:selectedKbId', ($event.target as HTMLSelectElement).value)"
          >
            <option value="">无</option>
            <option v-for="kb in knowledgeBases" :key="kb.id" :value="kb.id">
              {{ kb.name }}
            </option>
          </select>
        </div>
      </div>
    </div>

    <!-- 输入框：紧凑单行 -->
    <div class="input-box-container">
      <div class="input-with-suggestions">
        <input
          ref="inputElRef"
          :value="inputMessage"
          type="text"
          placeholder="输入消息..."
          :disabled="isStreaming"
          @input="onInput"
          @keydown.enter="$emit('send')"
          @keydown.down.prevent="$emit('suggestion-down')"
          @keydown.up.prevent="$emit('suggestion-up')"
          @keydown.esc="$emit('close-suggestions')"
          class="chat-input"
        />
        <div v-if="showSuggestions" class="suggestions-dropdown">
          <div
            v-for="(skill, index) in filteredSkills"
            :key="skill.name"
            class="suggestion-item"
            :class="{ active: selectedSuggestionIndex === index }"
            @click="$emit('select-suggestion', skill)"
          >
            <span class="suggestion-name">@{{ skill.name }}</span>
            <span class="suggestion-desc">{{ skill.description }}</span>
          </div>
        </div>
      </div>
      <Button
        class="send-btn-compact"
        variant="default"
        size="sm"
        :disabled="!inputMessage.trim() || isStreaming"
        @click="$emit('send')"
      >
        发送
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import Button from '@/components/ui/Button.vue'

defineProps<{
  inputMessage: string
  isStreaming: boolean
  selectedWorkflowId: string
  selectedKbId: string
  workflows: { id: string; name: string }[]
  knowledgeBases: { id: string; name: string }[]
  showSuggestions: boolean
  filteredSkills: { name: string; description: string }[]
  selectedSuggestionIndex: number
}>()

const emit = defineEmits<{
  'update:inputMessage': [value: string]
  'update:selectedWorkflowId': [value: string]
  'update:selectedKbId': [value: string]
  send: []
  'input-change': []
  'suggestion-down': []
  'suggestion-up': []
  'close-suggestions': []
  'select-suggestion': [skill: { name: string; description: string }]
}>()

const inputElRef = ref<HTMLInputElement | null>(null)

defineExpose({ inputElRef })

function onInput(event: Event) {
  const value = (event.target as HTMLInputElement).value
  emit('update:inputMessage', value)
  emit('input-change')
}
</script>

<style scoped src="./ChatInputBar.css"></style>
