export interface CitationSource {
  docId: string
  chunkIndex: number
  score: number
  text?: string
}

export interface Message {
  role: 'user' | 'assistant'
  content: string
  isStreaming?: boolean
  citations?: CitationSource[]
}

export interface Session {
  id: string
  title: string
  createdAt: number
  updatedAt: number
  messages: Message[]
}
