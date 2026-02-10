import type { Ref } from 'vue'
import type { Message } from './types'

interface EventHandlerContext {
  isStreaming: Ref<boolean>
  currentThought: Ref<string>
  scrollToBottom: () => void
}

export function handleSSEEventDispatch(
  eventType: string,
  data: Record<string, unknown>,
  lastMessage: Message | undefined,
  ctx: EventHandlerContext,
) {
  if (!lastMessage || lastMessage.role !== 'assistant') return

  switch (eventType) {
    case 'thought':
      handleThoughtEvent(data, ctx)
      break
    case 'token':
      lastMessage.content += data.content
      ctx.scrollToBottom()
      break
    case 'citation':
      handleCitationEvent(data, lastMessage)
      break
    case 'done':
      ctx.isStreaming.value = false
      lastMessage.isStreaming = false
      ctx.currentThought.value = ''
      break
    case 'error':
      lastMessage.content += `\n[\u9519\u8BEF: ${data.content || data.message || '\u672A\u77E5\u9519\u8BEF'}]`
      ctx.isStreaming.value = false
      lastMessage.isStreaming = false
      ctx.currentThought.value = ''
      break
  }
}

function handleThoughtEvent(data: Record<string, unknown>, ctx: EventHandlerContext) {
  if (data.type === 'workflow') {
    if (data.status === 'start') {
      ctx.currentThought.value = `\u5F00\u59CB\u6267\u884C\u5DE5\u4F5C\u6D41: ${data.workflow_name || ''}`
    }
  } else if (data.type === 'node') {
    const labels: Record<string, string> = {
      start: '\u5F00\u59CB',
      llm: '\u5927\u8BED\u8A00\u6A21\u578B',
      knowledge: '\u77E5\u8BC6\u5E93',
      condition: '\u6761\u4EF6',
      end: '\u7ED3\u675F',
    }
    const nodeType = (data.node_type as string) || ''
    if (data.status === 'start') {
      ctx.currentThought.value = `\u6267\u884C\u8282\u70B9: ${labels[nodeType] || nodeType || ''}`
    } else if (data.status === 'complete') {
      ctx.currentThought.value = `\u8282\u70B9\u5B8C\u6210: ${data.node_id || ''}`
    }
  } else if (data.type === 'condition') {
    ctx.currentThought.value = `\u6761\u4EF6\u5224\u65AD: ${data.expression || ''} \u2192 ${data.branch || ''}`
  } else if (data.type === 'retrieval') {
    handleRetrievalThought(data, ctx)
  } else {
    ctx.currentThought.value = (data.content as string) || ''
  }
}

function handleRetrievalThought(data: Record<string, unknown>, ctx: EventHandlerContext) {
  if (data.status === 'start') {
    ctx.currentThought.value = '\u6B63\u5728\u68C0\u7D22\u77E5\u8BC6\u5E93...'
  } else if (data.status === 'searching') {
    ctx.currentThought.value = '\u6B63\u5728\u641C\u7D22\u76F8\u5173\u6587\u6863...'
  } else if (data.status === 'complete') {
    const count = data.results_count || 0
    ctx.currentThought.value = `\u68C0\u7D22\u5B8C\u6210\uFF0C\u627E\u5230 ${count} \u4E2A\u76F8\u5173\u7247\u6BB5`
    setTimeout(() => {
      if (ctx.currentThought.value === `\u68C0\u7D22\u5B8C\u6210\uFF0C\u627E\u5230 ${count} \u4E2A\u76F8\u5173\u7247\u6BB5`) {
        ctx.currentThought.value = ''
      }
    }, 2000)
  } else if (data.status === 'error') {
    ctx.currentThought.value = '\u68C0\u7D22\u51FA\u9519: ' + (data.error || '\u672A\u77E5\u9519\u8BEF')
  }
}

function handleCitationEvent(data: Record<string, unknown>, lastMessage: Message) {
  if (data.sources && Array.isArray(data.sources)) {
    lastMessage.citations = data.sources.map(
      (s: { doc_id?: string; chunk_index?: number; score?: number; text?: string }) => ({
        docId: s.doc_id || '',
        chunkIndex: s.chunk_index || 0,
        score: s.score || 0,
        text: s.text,
      }),
    )
  } else if (data.content) {
    lastMessage.citations = [
      { docId: '', chunkIndex: 0, score: 0, text: data.content as string },
    ]
  }
}
