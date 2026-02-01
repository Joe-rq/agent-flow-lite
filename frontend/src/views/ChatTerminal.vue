<template>
  <div class="chat-terminal">
    <!-- 侧边栏：会话历史 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <button class="new-chat-btn" @click="createNewSession">
          <span class="icon">+</span>
          新建会话
        </button>
      </div>
      <div class="session-list">
        <div
          v-for="session in sessions"
          :key="session.id"
          class="session-item"
          :class="{ active: currentSessionId === session.id }"
          @click="switchSession(session.id)"
        >
          <div class="session-title">{{ session.title }}</div>
          <div class="session-time">{{ formatTime(session.updatedAt) }}</div>
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
          </div>
        </div>

        <!-- 思维链显示 -->
        <div v-if="currentThought" class="thought-chain">
          <div class="thought-icon">💭</div>
          <div class="thought-text">{{ currentThought }}</div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <div class="input-wrapper">
          <input
            v-model="inputMessage"
            type="text"
            placeholder="输入消息..."
            :disabled="isStreaming"
            @keydown.enter="sendMessage"
          />
          <button
            class="send-btn"
            :disabled="!inputMessage.trim() || isStreaming"
            @click="sendMessage"
          >
            发送
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import axios from 'axios'

// 类型定义
interface Message {
  role: 'user' | 'assistant'
  content: string
  isStreaming?: boolean
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

// 计算属性
const currentSession = computed(() => {
  return sessions.value.find(s => s.id === currentSessionId.value)
})

const currentMessages = computed(() => {
  return currentSession.value?.messages || []
})

// 方法
function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).substr(2)
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
}

function switchSession(sessionId: string) {
  currentSessionId.value = sessionId
  currentThought.value = ''
  scrollToBottom()
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
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
  // 使用 fetch API 发送 POST 请求建立 SSE 连接
  const response = await fetch('/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      message: message,
    }),
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

    for (const line of lines) {
      if (line.startsWith('data: ')) {
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
          handleSSEEvent(data, lastMessage)
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
}

function handleSSEEvent(data: any, lastMessage: Message | undefined) {
  if (!lastMessage || lastMessage.role !== 'assistant') return

  switch (data.type) {
    case 'thought':
      // 思维链
      currentThought.value = data.content
      break
    case 'token':
      // 打字机效果：逐字追加
      lastMessage.content += data.content
      scrollToBottom()
      break
    case 'citation':
      // 引用来源
      lastMessage.content += `\n[引用: ${data.content}]`
      break
    case 'done':
      // 完成
      isStreaming.value = false
      lastMessage.isStreaming = false
      currentThought.value = ''
      break
    case 'error':
      // 错误
      lastMessage.content += `\n[错误: ${data.content}]`
      isStreaming.value = false
      lastMessage.isStreaming = false
      currentThought.value = ''
      break
  }
}

// 初始化
onMounted(() => {
  // 创建一个默认会话
  if (sessions.value.length === 0) {
    createNewSession()
  }
})

// 监听消息变化，自动滚动
watch(currentMessages, () => {
  scrollToBottom()
}, { deep: true })
</script>

<style scoped>
.chat-terminal {
  display: flex;
  height: 100%;
  background-color: #f5f5f5;
}

/* 侧边栏 */
.sidebar {
  width: 260px;
  background-color: #fff;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #e0e0e0;
}

.new-chat-btn {
  width: 100%;
  padding: 12px 16px;
  background-color: #2c3e50;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: background-color 0.2s;
}

.new-chat-btn:hover {
  background-color: #34495e;
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
}

.session-item:hover {
  background-color: #f0f0f0;
}

.session-item.active {
  background-color: #e3f2fd;
}

.session-title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-time {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

/* 主聊天区域 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #fafafa;
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
  background-color: #e0e0e0;
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
  background-color: #2c3e50;
  color: white;
  border-bottom-right-radius: 4px;
}

.message-wrapper.assistant .message-bubble {
  background-color: #fff;
  color: #333;
  border: 1px solid #e0e0e0;
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
  background-color: #999;
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
  background-color: #fff3e0;
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
  color: #e65100;
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

/* 输入区域 */
.input-area {
  padding: 16px 20px;
  background-color: #fff;
  border-top: 1px solid #e0e0e0;
}

.input-wrapper {
  display: flex;
  gap: 12px;
  max-width: 800px;
  margin: 0 auto;
}

.input-wrapper input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 24px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.input-wrapper input:focus {
  border-color: #2c3e50;
}

.input-wrapper input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.send-btn {
  padding: 12px 24px;
  background-color: #2c3e50;
  color: white;
  border: none;
  border-radius: 24px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.send-btn:hover:not(:disabled) {
  background-color: #34495e;
}

.send-btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}
</style>
