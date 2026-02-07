<template>
  <div class="chat-terminal">
    <!-- 侧边栏：会话历史 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <Button class="new-chat-btn" variant="primary" @click="createNewSession">
          <span class="icon">+</span>
          新建会话
        </Button>
      </div>
      <div class="session-list">
        <div
          v-for="session in sessions"
          :key="session.id"
          class="session-item"
          :class="{ active: currentSessionId === session.id }"
          @click="switchSession(session.id)"
        >
          <div class="session-info">
            <div class="session-title">{{ session.title }}</div>
            <div class="session-time">{{ formatTime(session.updatedAt) }}</div>
          </div>
          <button
            class="session-delete-btn"
            @click.stop="deleteSession(session.id)"
            title="删除会话"
          >
            ×
          </button>
        </div>
      </div>
    </aside>

    <!-- 主聊天区域 -->
    <main class="chat-main">
      <!-- 消息列表 -->
      <div ref="messagesContainer" class="messages-container">
        <div
          v-for="(message, index) in currentMessages"
          :key="index"
          class="message-wrapper"
          :class="message.role"
        >
          <div class="message-avatar">
            {{ message.role === 'user' ? '👤' : '🤖' }}
          </div>
          <div class="message-content">
            <div class="message-bubble">
              {{ message.content }}
            </div>
            <div v-if="message.role === 'assistant' && message.isStreaming" class="typing-indicator">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
            </div>
            <div
              v-if="message.role === 'assistant' && message.citations?.length"
              class="citation-list"
            >
              <button
                v-for="(citation, idx) in message.citations"
                :key="`${citation.docId}-${citation.chunkIndex}-${idx}`"
                class="citation-item"
                @click="openCitation(citation)"
              >
                引用{{ idx + 1 }}
              </button>
            </div>
          </div>
        </div>

        <!-- 思维链显示 -->
        <div v-if="currentThought" class="thought-chain">
          <div class="thought-icon">💭</div>
          <div class="thought-text">{{ currentThought }}</div>
        </div>
      </div>

      <div v-if="activeCitation" class="citation-panel">
        <div class="citation-panel-header">
          <div class="citation-title">引用详情</div>
          <button class="citation-close" @click="closeCitation">×</button>
        </div>
        <div class="citation-meta">
          <span>doc: {{ activeCitation.docId || '未知' }}</span>
          <span>chunk: {{ activeCitation.chunkIndex }}</span>
          <span>score: {{ activeCitation.score.toFixed(2) }}</span>
        </div>
        <div class="citation-excerpt">
          <mark class="citation-highlight">
            {{ activeCitation.text || '暂无引用内容' }}
          </mark>
        </div>
      </div>

      <!-- 现代聊天输入区（模仿图二风格） -->
      <div class="composer-container">
        <!-- 顶部配置栏 -->
        <div class="composer-header">
          <div class="config-chips">
            <div class="config-chip">
              <span class="chip-label">工作流</span>
              <select v-model="selectedWorkflowId" :disabled="isStreaming" class="chip-select">
                <option value="">无</option>
                <option v-for="wf in workflows" :key="wf.id" :value="wf.id">
                  {{ wf.name }}
                </option>
              </select>
            </div>
            <div class="config-chip">
              <span class="chip-label">知识库</span>
              <select
                v-model="selectedKbId"
                :disabled="isStreaming || !!selectedWorkflowId"
                class="chip-select"
              >
                <option value="">无</option>
                <option v-for="kb in knowledgeBases" :key="kb.id" :value="kb.id">
                  {{ kb.name }}
                </option>
              </select>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="composer-body">
          <div class="input-with-suggestions">
            <textarea
              ref="inputRef"
              v-model="inputMessage"
              placeholder="尽管问，带图也行..."
              :disabled="isStreaming"
              @keydown.enter.prevent="handleEnter"
              @input="onInputChange"
              @keydown.down.prevent="onSuggestionDown"
              @keydown.up.prevent="onSuggestionUp"
              @keydown.esc="closeSuggestions"
              rows="1"
              class="composer-textarea"
            ></textarea>
            <div v-if="showSuggestions" class="suggestions-dropdown">
              <div
                v-for="(skill, index) in filteredSkills"
                :key="skill.name"
                class="suggestion-item"
                :class="{ active: selectedSuggestionIndex === index }"
                @click="selectSuggestion(skill)"
              >
                <span class="suggestion-name">@{{ skill.name }}</span>
                <span class="suggestion-desc">{{ skill.description }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 底部工具栏 -->
        <div class="composer-footer">
          <button class="upload-btn" title="上传文件" @click="handleUpload">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 5v14M5 12h14"/>
            </svg>
          </button>
          <div class="footer-actions">
            <Button
              class="send-btn"
              variant="primary"
              :disabled="!inputMessage.trim() || isStreaming"
              @click="sendMessage"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="send-icon">
                <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
              </svg>
            </Button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import Button from '@/components/ui/Button.vue'

// 类型定义
interface CitationSource {
  docId: string
  chunkIndex: number
  score: number
  text?: string
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  isStreaming?: boolean
  citations?: CitationSource[]
}

interface Session {
  id: string
  title: string
  createdAt: number
  updatedAt: number
  messages: Message[]
}

// 状态
const sessions = ref<Session[]>([])
const currentSessionId = ref<string>('')
const inputMessage = ref('')
const isStreaming = ref(false)
const currentThought = ref('')
const messagesContainer = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLInputElement | null>(null)
const selectedWorkflowId = ref<string>('')
const selectedKbId = ref<string>('')
const workflows = ref<{ id: string; name: string }[]>([])
const knowledgeBases = ref<{ id: string; name: string }[]>([])
const activeCitation = ref<CitationSource | null>(null)

// Skill 自动补全状态
const skills = ref<{ name: string; description: string }[]>([])
const showSuggestions = ref(false)
const filteredSkills = ref<{ name: string; description: string }[]>([])
const selectedSuggestionIndex = ref(0)

const authStore = useAuthStore()

// 计算属性
const currentSession = computed(() => {
  return sessions.value.find(s => s.id === currentSessionId.value)
})

const currentMessages = computed(() => {
  return currentSession.value?.messages || []
})

// 方法
function generateId(): string {
  if (crypto && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  const array = new Uint8Array(16)
  crypto.getRandomValues(array)
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
}

function formatTime(timestamp: number): string {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function createNewSession() {
  const newSession: Session = {
    id: generateId(),
    title: '新会话 ' + (sessions.value.length + 1),
    createdAt: Date.now(),
    updatedAt: Date.now(),
    messages: [],
  }
  sessions.value.unshift(newSession)
  currentSessionId.value = newSession.id
  currentThought.value = ''
  activeCitation.value = null
}

// 删除会话
async function deleteSession(sessionId: string) {
  if (!confirm('确定要删除此会话吗？')) return

  try {
    await axios.delete(`/api/v1/chat/sessions/${sessionId}`)
    sessions.value = sessions.value.filter(s => s.id !== sessionId)

    // 如果删除的是当前会话，切换到第一个会话或创建新会话
    if (currentSessionId.value === sessionId) {
      const firstSession = sessions.value[0]
      if (firstSession) {
        currentSessionId.value = firstSession.id
      } else {
        createNewSession()
      }
    }
  } catch (error) {
    console.error('删除会话失败:', error)
    // 即使后端删除失败，也从本地移除（可能是本地创建的会话）
    sessions.value = sessions.value.filter(s => s.id !== sessionId)
    if (currentSessionId.value === sessionId) {
      const firstSession = sessions.value[0]
      if (firstSession) {
        currentSessionId.value = firstSession.id
      } else {
        createNewSession()
      }
    }
  }
}



function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 处理 Enter 键（Shift+Enter 换行，Enter 发送）
function handleEnter(event: KeyboardEvent) {
  if (!event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

// 处理上传按钮点击
function handleUpload() {
  // 触发文件选择
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.txt,.md,.pdf,.doc,.docx'
  input.onchange = (e) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (file) {
      console.log('选择的文件:', file.name)
      // TODO: 实现文件上传逻辑
      alert('文件上传功能开发中: ' + file.name)
    }
  }
  input.click()
}

// textarea 自动高度
function autoResizeTextarea() {
  nextTick(() => {
    const textarea = inputRef.value
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px'
    }
  })
}

async function sendMessage() {
  const message = inputMessage.value.trim()
  if (!message || isStreaming.value) return

  // 如果没有当前会话，创建一个新会话
  if (!currentSession.value) {
    createNewSession()
  }

  const session = currentSession.value!

  // 添加用户消息
  session.messages.push({
    role: 'user',
    content: message,
  })

  // 更新会话标题（如果是第一条消息）
  if (session.messages.length === 1) {
    session.title = message.slice(0, 20) + (message.length > 20 ? '...' : '')
  }

  inputMessage.value = ''
  isStreaming.value = true
  currentThought.value = ''
  activeCitation.value = null

  // 添加 AI 消息占位
  session.messages.push({
    role: 'assistant',
    content: '',
    isStreaming: true,
  })

  scrollToBottom()

  // 使用 SSE 连接
  try {
    await connectSSE(session.id, message)
  } catch (error: any) {
    console.error('SSE connection error:', error)
    const lastMessage = session.messages[session.messages.length - 1]
    if (lastMessage && lastMessage.role === 'assistant') {
      lastMessage.content = '连接错误: ' + (error.message || '请重试')
      lastMessage.isStreaming = false
    }
    isStreaming.value = false
    currentThought.value = ''
    alert('发送消息失败: ' + (error.message || '请检查网络连接'))
  }

  session.updatedAt = Date.now()
}

async function connectSSE(sessionId: string, message: string) {
  const payload = buildChatPayload(sessionId, message)
  // 使用 fetch API 发送 POST 请求建立 SSE 连接
  const response = await fetch('/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authStore.token}`,
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  const reader = response.body?.getReader()
  const decoder = new TextDecoder()

  if (!reader) {
    throw new Error('No response body')
  }

  const session = currentSession.value!
  const lastMessage = session.messages[session.messages.length - 1]

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
          isStreaming.value = false
          if (lastMessage) {
            lastMessage.isStreaming = false
          }
          currentThought.value = ''
          return
        }

        try {
          const data = JSON.parse(dataStr)
          handleSSEEvent(currentEvent, data, lastMessage)
        } catch (e) {
          // 忽略解析错误
        }
      }
    }
  }

  isStreaming.value = false
  if (lastMessage) {
    lastMessage.isStreaming = false
  }
  currentThought.value = ''
  activeCitation.value = null
}

function buildChatPayload(sessionId: string, message: string) {
  return {
    session_id: sessionId,
    message: message,
    workflow_id: selectedWorkflowId.value || undefined,
    kb_id: selectedKbId.value || undefined,
  }
}

async function loadWorkflows() {
  try {
    const response = await axios.get('/api/v1/workflows')
    workflows.value = (response.data.items || []).map((wf: any) => ({
      id: wf.id,
      name: wf.name
    }))
  } catch (error) {
    console.error('加载工作流列表失败:', error)
  }
}

async function loadKnowledgeBases() {
  try {
    const response = await axios.get('/api/v1/knowledge')
    const items = response.data.items || response.data || []
    knowledgeBases.value = items.map((kb: any) => ({
      id: kb.id || kb.kb_id,
      name: kb.name || kb.kb_name || '未命名知识库'
    }))
  } catch (error) {
    console.error('加载知识库列表失败:', error)
  }
}

async function loadSkills() {
  try {
    const response = await axios.get('/api/v1/skills')
    const items = response.data.skills || []
    skills.value = items.map((s: any) => ({
      name: s.name,
      description: s.description || ''
    }))
  } catch (error) {
    console.error('加载技能列表失败:', error)
    skills.value = []
  }
}

function onInputChange() {
  // 自动调整 textarea 高度
  autoResizeTextarea()

  const text = inputMessage.value
  const atIndex = text.lastIndexOf('@')

  if (atIndex === -1) {
    showSuggestions.value = false
    return
  }

  const afterAt = text.slice(atIndex + 1)
  const hasSpace = afterAt.includes(' ')

  if (hasSpace) {
    showSuggestions.value = false
    return
  }

  const query = afterAt.toLowerCase()
  filteredSkills.value = skills.value.filter(skill =>
    skill.name.toLowerCase().includes(query)
  )

  if (filteredSkills.value.length > 0) {
    showSuggestions.value = true
    selectedSuggestionIndex.value = 0
  } else {
    showSuggestions.value = false
  }
}

function onSuggestionDown() {
  if (!showSuggestions.value) return
  selectedSuggestionIndex.value =
    (selectedSuggestionIndex.value + 1) % filteredSkills.value.length
}

function onSuggestionUp() {
  if (!showSuggestions.value) return
  selectedSuggestionIndex.value =
    (selectedSuggestionIndex.value - 1 + filteredSkills.value.length) %
    filteredSkills.value.length
}

function closeSuggestions() {
  showSuggestions.value = false
}

function selectSuggestion(skill: { name: string; description: string }) {
  const text = inputMessage.value
  const atIndex = text.lastIndexOf('@')
  inputMessage.value = text.slice(0, atIndex) + '@' + skill.name + ' '
  showSuggestions.value = false
  inputRef.value?.focus()
}

async function loadSessions() {
  try {
    const response = await axios.get('/api/v1/chat/sessions')
    const items = response.data.sessions || []
    sessions.value = items.map((s: any) => ({
      id: s.session_id,
      title: s.title || '新会话',
      createdAt: new Date(s.created_at).getTime(),
      updatedAt: new Date(s.updated_at).getTime(),
      messages: []
    }))
    const firstSession = sessions.value[0]
    if (firstSession) {
      currentSessionId.value = firstSession.id
    }
  } catch (error) {
    console.error('加载会话列表失败:', error)
  }
}

function handleSSEEvent(eventType: string, data: any, lastMessage: Message | undefined) {
  if (!lastMessage || lastMessage.role !== 'assistant') return

  switch (eventType) {
    case 'thought':
      // 思维链 - 处理 RAG 检索状态
      if (data.type === 'workflow') {
        if (data.status === 'start') {
          currentThought.value = `开始执行工作流: ${data.workflow_name || ''}`
        }
      } else if (data.type === 'node') {
        if (data.status === 'start') {
          const labels: Record<string, string> = {
            start: '开始',
            llm: 'LLM',
            knowledge: '知识库',
            condition: '条件',
            end: '结束'
          }
          currentThought.value = `执行节点: ${labels[data.node_type] || data.node_type || ''}`
        } else if (data.status === 'complete') {
          currentThought.value = `节点完成: ${data.node_id || ''}`
        }
      } else if (data.type === 'condition') {
        currentThought.value = `条件判断: ${data.expression || ''} → ${data.branch || ''}`
      } else if (data.type === 'retrieval') {
        if (data.status === 'start') {
          currentThought.value = '正在检索知识库...'
        } else if (data.status === 'searching') {
          currentThought.value = '正在搜索相关文档...'
        } else if (data.status === 'complete') {
          const count = data.results_count || 0
          currentThought.value = `检索完成，找到 ${count} 个相关片段`
          // 延迟清除思维链
          setTimeout(() => {
            if (currentThought.value === `检索完成，找到 ${count} 个相关片段`) {
              currentThought.value = ''
            }
          }, 2000)
        } else if (data.status === 'error') {
          currentThought.value = '检索出错: ' + (data.error || '未知错误')
        }
      } else {
        currentThought.value = data.content || ''
      }
      break
    case 'token':
      // 打字机效果：逐字追加
      lastMessage.content += data.content
      scrollToBottom()
      break
    case 'citation':
      // 引用来源 - 处理 sources 数组
      if (data.sources && Array.isArray(data.sources)) {
        lastMessage.citations = data.sources.map((s: any) => ({
          docId: s.doc_id || '',
          chunkIndex: s.chunk_index || 0,
          score: s.score || 0,
          text: s.text
        }))
      } else if (data.content) {
        lastMessage.citations = [
          {
            docId: '',
            chunkIndex: 0,
            score: 0,
            text: data.content
          }
        ]
      }
      break
    case 'done':
      // 完成
      isStreaming.value = false
      lastMessage.isStreaming = false
      currentThought.value = ''
      break
    case 'error':
      // 错误
      lastMessage.content += `\n[错误: ${data.content || data.message || '未知错误'}]`
      isStreaming.value = false
      lastMessage.isStreaming = false
      currentThought.value = ''
      break
  }
}

function openCitation(source: CitationSource) {
  activeCitation.value = source
}

function closeCitation() {
  activeCitation.value = null
}

// 从后端加载会话历史
async function loadSessionHistory(sessionId: string) {
  try {
    const response = await axios.get(`/api/v1/chat/sessions/${sessionId}`)
    const data = response.data
    if (data && data.messages) {
      const session = currentSession.value
      if (session) {
        session.messages = data.messages.map((msg: any) => ({
          role: msg.role,
          content: msg.content,
          isStreaming: false
        }))
      }
    }
  } catch (error) {
    console.error('加载会话历史失败:', error)
    // 如果加载失败，保持当前内存中的会话
  }
}

// 切换会话时加载历史
async function switchSession(sessionId: string) {
  currentSessionId.value = sessionId
  currentThought.value = ''
  await loadSessionHistory(sessionId)
  scrollToBottom()
}

// 初始化
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

// 监听消息变化，自动滚动
watch(currentMessages, () => {
  scrollToBottom()
}, { deep: true })

watch(selectedWorkflowId, (value) => {
  if (value) {
    selectedKbId.value = ''
  }
})
</script>

<style scoped>
.chat-terminal {
  display: flex;
  height: 100%;
  background-color: var(--bg-primary);
}

/* 侧边栏 */
.sidebar {
  width: 260px;
  background-color: var(--surface-primary);
  border-right: 1px solid var(--border-primary);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-primary);
}

.new-chat-btn {
  width: 100%;
  gap: 8px;
}

.new-chat-btn .icon {
  font-size: 18px;
  font-weight: bold;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
  margin-bottom: 4px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.session-item:hover {
  background-color: var(--bg-tertiary);
}

.session-item.active {
  background-color: var(--accent-cyan-soft);
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-time {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}

.session-delete-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-size: 18px;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.2s;
  flex-shrink: 0;
}

.session-item:hover .session-delete-btn {
  opacity: 1;
}

.session-delete-btn:hover {
  background-color: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

/* 主聊天区域 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-primary);
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 消息样式 */
.message-wrapper {
  display: flex;
  gap: 12px;
  max-width: 80%;
}

.message-wrapper.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-wrapper.assistant {
  align-self: flex-start;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.message-wrapper.user .message-bubble {
  background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
  color: white;
  border-bottom-right-radius: 4px;
}

.message-wrapper.assistant .message-bubble {
  background-color: var(--surface-primary);
  color: var(--text-primary);
  border: 1px solid var(--border-primary);
  border-bottom-left-radius: 4px;
}

/* 打字机效果指示器 */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 0;
}

.typing-indicator .dot {
  width: 6px;
  height: 6px;
  background-color: var(--text-muted);
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator .dot:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator .dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-4px);
  }
}

/* 思维链 */
.thought-chain {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background-color: var(--accent-purple-soft);
  border-radius: 8px;
  margin: 0 auto;
  max-width: 60%;
  animation: fadeIn 0.3s ease;
}

.thought-icon {
  font-size: 16px;
}

.thought-text {
  font-size: 13px;
  color: var(--accent-purple);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 引用列表 */
.citation-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 6px;
}

.citation-item {
  border: 1px solid var(--border-primary);
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
  border-radius: 12px;
  padding: 4px 10px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.citation-item:hover {
  border-color: var(--accent-cyan);
  color: var(--text-primary);
}

/* 引用面板 */
.citation-panel {
  border-top: 1px solid var(--border-primary);
  background-color: var(--surface-primary);
  padding: 12px 20px;
}

.citation-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.citation-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.citation-close {
  border: none;
  background: transparent;
  font-size: 18px;
  color: var(--text-muted);
  cursor: pointer;
}

.citation-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.citation-excerpt {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.6;
}

.citation-highlight {
  background: #fef3c7;
  color: #92400e;
  padding: 2px 4px;
  border-radius: 4px;
}

/* 现代聊天输入区（模仿图二风格） */
.composer-container {
  margin: 0 20px 20px;
  background-color: var(--surface-primary);
  border: 1px solid var(--border-primary);
  border-radius: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

/* 顶部配置栏 */
.composer-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-primary);
  background-color: var(--bg-tertiary);
}

.config-chips {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.config-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background-color: var(--surface-primary);
  border: 1px solid var(--border-primary);
  border-radius: 20px;
  font-size: 13px;
}

.chip-label {
  color: var(--text-secondary);
  font-weight: 500;
}

.chip-select {
  border: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
  outline: none;
  padding: 0;
  min-width: 80px;
}

.chip-select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 输入区域 */
.composer-body {
  padding: 16px 20px;
  position: relative;
}

.composer-textarea {
  width: 100%;
  min-height: 24px;
  max-height: 200px;
  border: none;
  outline: none;
  resize: none;
  font-size: 15px;
  line-height: 1.5;
  color: var(--text-primary);
  background: transparent;
  font-family: inherit;
}

.composer-textarea::placeholder {
  color: var(--text-secondary);
}

.composer-textarea:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 底部工具栏 */
.composer-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-top: 1px solid var(--border-primary);
  background-color: var(--bg-tertiary);
}

.upload-btn {
  width: 36px;
  height: 36px;
  border: 1px solid var(--border-primary);
  border-radius: 50%;
  background-color: var(--surface-primary);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.upload-btn:hover {
  border-color: var(--accent-cyan);
  color: var(--accent-cyan);
}

.upload-btn svg {
  width: 18px;
  height: 18px;
}

.footer-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.send-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-icon {
  width: 18px;
  height: 18px;
}

/* Skill 自动补全下拉框 */
.input-with-suggestions {
  position: relative;
  flex: 1;
}

.suggestions-dropdown {
  position: absolute;
  bottom: 100%;
  left: 0;
  right: 0;
  background-color: var(--surface-primary);
  border: 1px solid var(--border-primary);
  border-radius: 12px;
  margin-bottom: 8px;
  max-height: 200px;
  overflow-y: auto;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  z-index: 100;
}

.suggestion-item {
  padding: 10px 16px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: background-color 0.15s;
}

.suggestion-item:hover,
.suggestion-item.active {
  background-color: var(--bg-tertiary);
}

.suggestion-item:first-child {
  border-radius: 12px 12px 0 0;
}

.suggestion-item:last-child {
  border-radius: 0 0 12px 12px;
}

.suggestion-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--accent-cyan);
}

.suggestion-desc {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 桌面端优化 */
@media (min-width: 1200px) {
  .composer-container {
    margin: 0 40px 24px;
    max-width: 900px;
    margin-left: auto;
    margin-right: auto;
  }
}
</style>
