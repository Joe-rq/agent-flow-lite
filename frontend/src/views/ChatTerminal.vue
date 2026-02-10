<template>
  <div class="chat-terminal">
    <!-- 侧边栏：会话历史 -->
    <ChatSidebar
      :sessions="sessions"
      :current-session-id="currentSessionId"
      @create-session="createNewSession"
      @switch-session="switchSession"
      @delete-session="deleteSession"
    />

    <!-- 主聊天区域 -->
    <main class="chat-main">
      <!-- 消息列表 -->
      <ChatMessageList
        ref="messageListRef"
        :current-messages="currentMessages"
        :current-thought="currentThought"
        :active-citation="activeCitation"
        @open-citation="openCitation"
        @close-citation="closeCitation"
      />

      <!-- 聊天输入区 -->
      <ChatInputBar
        ref="inputBarRef"
        :input-message="inputMessage"
        :is-streaming="isStreaming"
        :selected-workflow-id="selectedWorkflowId"
        :selected-kb-id="selectedKbId"
        :workflows="workflows"
        :knowledge-bases="knowledgeBases"
        :show-suggestions="showSuggestions"
        :filtered-skills="filteredSkills"
        :selected-suggestion-index="selectedSuggestionIndex"
        @update:input-message="inputMessage = $event"
        @update:selected-workflow-id="selectedWorkflowId = $event"
        @update:selected-kb-id="selectedKbId = $event"
        @send="handleSend"
        @input-change="onInputChange"
        @suggestion-down="onSuggestionDown"
        @suggestion-up="onSuggestionUp"
        @close-suggestions="closeSuggestions"
        @select-suggestion="selectSuggestion"
      />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import ChatSidebar from '@/components/chat/ChatSidebar.vue'
import ChatMessageList from '@/components/chat/ChatMessageList.vue'
import ChatInputBar from '@/components/chat/ChatInputBar.vue'
import { useChatSession } from '@/composables/chat/useChatSession'
import { useChatSSE } from '@/composables/chat/useChatSSE'
import { useSkillAutocomplete } from '@/composables/useSkillAutocomplete'

// Template refs for child components
const messageListRef = ref<InstanceType<typeof ChatMessageList> | null>(null)
const inputBarRef = ref<InstanceType<typeof ChatInputBar> | null>(null)

// Computed ref to forward messagesContainer from child component
const messagesContainer = computed(() => messageListRef.value?.containerRef ?? null)
const inputRef = computed(() => inputBarRef.value?.inputElRef ?? null)

// Local state
const selectedWorkflowId = ref<string>('')
const selectedKbId = ref<string>('')
const workflows = ref<{ id: string; name: string }[]>([])
const knowledgeBases = ref<{ id: string; name: string }[]>([])

// --- Composable: useChatSession ---
const {
  sessions,
  currentSessionId,
  activeCitation,
  currentSession,
  currentMessages,
  createNewSession,
  deleteSession,
  loadSessions,
  switchSession,
  openCitation,
  closeCitation,
} = useChatSession()

// --- Composable: useChatSSE ---
const {
  isStreaming,
  currentThought,
  buildChatPayload,
  handleSSEEvent,
  sendMessage,
  connectSSE,
  scrollToBottom,
} = useChatSSE({
  currentSession,
  currentSessionId,
  selectedWorkflowId,
  selectedKbId,
  messagesContainer,
  activeCitation,
  createNewSession,
})

// --- Composable: useSkillAutocomplete ---
const {
  skills,
  inputMessage,
  showSuggestions,
  filteredSkills,
  selectedSuggestionIndex,
  loadSkills,
  onInputChange,
  onSuggestionDown,
  onSuggestionUp,
  closeSuggestions,
  selectSuggestion,
} = useSkillAutocomplete(inputRef)

// Data loaders
function handleSend() {
  sendMessage(inputMessage)
}

async function loadWorkflows() {
  try {
    const response = await axios.get('/api/v1/workflows')
    workflows.value = (response.data.items || []).map((wf: { id: string; name: string }) => ({
      id: wf.id,
      name: wf.name,
    }))
  } catch (error) {
    console.error('\u52A0\u8F7D\u5DE5\u4F5C\u6D41\u5217\u8868\u5931\u8D25:', error)
  }
}

async function loadKnowledgeBases() {
  try {
    const response = await axios.get('/api/v1/knowledge')
    const items = response.data.items || response.data || []
    knowledgeBases.value = items.map(
      (kb: { id?: string; kb_id?: string; name?: string; kb_name?: string }) => ({
        id: kb.id || kb.kb_id,
        name: kb.name || kb.kb_name || '\u672A\u547D\u540D\u77E5\u8BC6\u5E93',
      }),
    )
  } catch (error) {
    console.error('\u52A0\u8F7D\u77E5\u8BC6\u5E93\u5217\u8868\u5931\u8D25:', error)
  }
}

// Lifecycle
onMounted(() => {
  loadSessions().finally(() => {
    if (sessions.value.length === 0) {
      createNewSession()
    }
  })
  loadWorkflows()
  loadKnowledgeBases()
  loadSkills()
})

// Watchers
watch(currentMessages, () => {
  scrollToBottom()
}, { deep: true })

watch(selectedWorkflowId, (value) => {
  if (value) {
    selectedKbId.value = ''
  }
})
</script>

<style scoped src="./ChatTerminal.css"></style>
