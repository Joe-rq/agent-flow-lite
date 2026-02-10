<template>
  <div class="document-list">
    <h3>文档列表</h3>
    <div v-if="documents.length === 0" class="empty-docs">
      <p>暂无文档，请上传文件</p>
    </div>
    <div v-else class="docs-table">
      <div class="docs-header">
        <span class="col-name">文件名</span>
        <span class="col-status">状态</span>
        <span class="col-size">大小</span>
        <span class="col-action">操作</span>
      </div>
      <div
        v-for="doc in documents"
        :key="doc.id"
        class="docs-row"
      >
        <span class="col-name" :title="doc.fileName">
          {{ doc.fileName }}
        </span>
        <span class="col-status">
          <span class="status-badge" :class="doc.status">
            {{ getDocStatusText(doc.status) }}
          </span>
        </span>
        <span class="col-size">{{ formatFileSize(doc.fileSize) }}</span>
        <span class="col-action">
          <button
            class="btn-delete"
            :disabled="doc.status === 'processing'"
            @click="$emit('delete-document', doc.id)"
          >
            删除
          </button>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatFileSize } from '@/utils/format'
import type { Document } from '@/types'

defineProps<{
  documents: Document[]
  getDocStatusText: (status: Document['status']) => string
}>()

defineEmits<{
  'delete-document': [docId: string]
}>()
</script>

<style scoped src="./KbDocumentTable.css"></style>
