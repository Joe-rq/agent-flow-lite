import { ref, computed } from 'vue'
import axios from 'axios'
import type { CitationSource, Session } from './types'

export function useChatSession() {
  const sessions = ref<Session[]>([])
  const currentSessionId = ref<string>('')
  const activeCitation = ref<CitationSource | null>(null)

  const currentSession = computed(() => {
    return sessions.value.find((s) => s.id === currentSessionId.value)
  })

  const currentMessages = computed(() => {
    return currentSession.value?.messages || []
  })

  function generateId(): string {
    if (crypto && typeof crypto.randomUUID === 'function') {
      return crypto.randomUUID()
    }
    const array = new Uint8Array(16)
    crypto.getRandomValues(array)
    return Array.from(array, (byte) => byte.toString(16).padStart(2, '0')).join('')
  }

  function createNewSession() {
    const newSession: Session = {
      id: generateId(),
      title: '\u65B0\u4F1A\u8BDD ' + (sessions.value.length + 1),
      createdAt: Date.now(),
      updatedAt: Date.now(),
      messages: [],
    }
    sessions.value.unshift(newSession)
    currentSessionId.value = newSession.id
    activeCitation.value = null
  }

  async function deleteSession(sessionId: string) {
    if (!confirm('\u786E\u5B9A\u8981\u5220\u9664\u6B64\u4F1A\u8BDD\u5417\uFF1F')) return

    const removeAndSwitch = () => {
      sessions.value = sessions.value.filter((s) => s.id !== sessionId)
      if (currentSessionId.value === sessionId) {
        const firstSession = sessions.value[0]
        if (firstSession) {
          currentSessionId.value = firstSession.id
        } else {
          createNewSession()
        }
      }
    }

    try {
      await axios.delete(`/api/v1/chat/sessions/${sessionId}`)
      removeAndSwitch()
    } catch (error) {
      console.error('\u5220\u9664\u4F1A\u8BDD\u5931\u8D25:', error)
      removeAndSwitch()
    }
  }

  async function loadSessions() {
    try {
      const response = await axios.get('/api/v1/chat/sessions')
      const items = response.data.sessions || []
      sessions.value = items.map(
        (s: { session_id: string; title?: string; created_at: string; updated_at: string }) => ({
          id: s.session_id,
          title: s.title || '\u65B0\u4F1A\u8BDD',
          createdAt: new Date(s.created_at).getTime(),
          updatedAt: new Date(s.updated_at).getTime(),
          messages: [],
        }),
      )
      const firstSession = sessions.value[0]
      if (firstSession) {
        currentSessionId.value = firstSession.id
      }
    } catch (error) {
      console.error('\u52A0\u8F7D\u4F1A\u8BDD\u5217\u8868\u5931\u8D25:', error)
    }
  }

  async function loadSessionHistory(sessionId: string) {
    try {
      const response = await axios.get(`/api/v1/chat/sessions/${sessionId}`)
      const data = response.data
      if (data && data.messages) {
        const session = currentSession.value
        if (session) {
          session.messages = data.messages.map((msg: { role: string; content: string }) => ({
            role: msg.role,
            content: msg.content,
            isStreaming: false,
          }))
        }
      }
    } catch (error) {
      console.error('\u52A0\u8F7D\u4F1A\u8BDD\u5386\u53F2\u5931\u8D25:', error)
    }
  }

  async function switchSession(sessionId: string) {
    currentSessionId.value = sessionId
    await loadSessionHistory(sessionId)
  }

  function openCitation(source: CitationSource) {
    activeCitation.value = source
  }

  function closeCitation() {
    activeCitation.value = null
  }

  return {
    sessions,
    currentSessionId,
    activeCitation,
    currentSession,
    currentMessages,
    generateId,
    createNewSession,
    deleteSession,
    loadSessions,
    loadSessionHistory,
    switchSession,
    openCitation,
    closeCitation,
  }
}
