export interface User {
  id: number
  email: string
  role: 'admin' | 'user'
  is_active: boolean
  created_at: string
}

export interface SkillInput {
  name: string
  label?: string
  type?: 'text' | 'textarea'
  description?: string
  required?: boolean
  default?: string
}

export interface Skill {
  name: string
  description?: string
  inputs: SkillInput[]
  updatedAt: string
}

export interface SkillApiItem {
  name: string
  description?: string
  inputs?: SkillInput[]
  updated_at?: string
  updatedAt?: string
}

export interface KnowledgeBase {
  id: string
  name: string
  documentCount: number
  createdAt: string
}

export interface Document {
  id: string
  fileName: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  fileSize: number
  createdAt: string
}

export interface UploadTask {
  id: string
  fileName: string
  fileSize: number
  progress: number
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'failed'
  file: File
}

export interface SearchResult {
  text: string
  score: number
  metadata?: {
    doc_id?: string
    chunk_index?: number
  }
}
