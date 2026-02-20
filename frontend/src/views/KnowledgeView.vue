<template>
  <div class="knowledge-view">
    <div class="page-header">
      <h1>知识库管理</h1>
      <Button variant="primary" @click="showCreateDialog = true">
        + 新建知识库
      </Button>
    </div>

    <!-- 知识库列表 -->
    <div v-if="!selectedKB" class="kb-list">
      <div
        v-for="kb in knowledgeBases"
        :key="kb.id"
        class="kb-card"
        @click="selectKnowledgeBase(kb)"
      >
        <div class="kb-card-header">
          <h3 class="kb-name">{{ kb.name }}</h3>
          <span class="kb-doc-count">{{ kb.documentCount }} 文档</span>
        </div>
        <div class="kb-card-footer">
          <span class="kb-created">创建于 {{ formatDate(kb.createdAt) }}</span>
          <Button
            variant="danger"
            size="sm"
            @click.stop="deleteKnowledgeBase(kb.id, kb.name)"
          >
            删除
          </Button>
        </div>
      </div>

      <div v-if="knowledgeBases.length === 0" class="empty-state">
        <p>暂无知识库</p>
        <Button variant="primary" @click="showCreateDialog = true">
          创建第一个知识库
        </Button>
      </div>
    </div>

    <!-- 知识库详情 -->
    <div v-else class="kb-detail">
      <div class="kb-detail-header">
        <Button variant="secondary" size="sm" @click="selectedKB = null">← 返回列表</Button>
        <h2>{{ selectedKB.name }}</h2>
        <span class="kb-meta">{{ documents.length }} 个文档</span>
      </div>

      <KbUploadArea
        :is-dragging="isDragging"
        :upload-tasks="uploadTasks"
        :get-status-text="getStatusText"
        ref="uploadAreaRef"
        @trigger-file-input="triggerUploadFileInput"
        @drop="handleDrop"
        @file-select="handleFileSelect"
        @update:is-dragging="isDragging = $event"
      />

      <KbSearchTest
        v-model:search-query="searchQuery"
        :search-results="searchResults"
        :is-searching="isSearching"
        :search-error="searchError"
        @search="performSearch"
      />

      <KbDocumentTable
        :documents="documents"
        :get-doc-status-text="getDocStatusText"
        @delete-document="deleteDocument"
      />
    </div>

    <!-- 创建知识库对话框 -->
    <div v-if="showCreateDialog" class="dialog-overlay" @click.self="showCreateDialog = false">
      <div class="dialog">
        <h3>新建知识库</h3>
        <div class="form-group">
          <label>知识库名称</label>
          <TextInput
            v-model="newKBName"
            type="text"
            placeholder="请输入知识库名称"
            @keyup.enter="createKnowledgeBase"
          />
        </div>
        <div class="dialog-actions">
          <Button variant="secondary" @click="showCreateDialog = false">
            取消
          </Button>
          <Button
            variant="primary"
            :disabled="!newKBName.trim()"
            @click="createKnowledgeBase"
          >
            创建
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import Button from '@/components/ui/Button.vue'
import { TextInput } from '@/components/ui'
import KbUploadArea from '@/components/knowledge/KbUploadArea.vue'
import KbSearchTest from '@/components/knowledge/KbSearchTest.vue'
import KbDocumentTable from '@/components/knowledge/KbDocumentTable.vue'
import { formatDate } from '@/utils/format'
import { useKnowledgeApi } from '@/composables/knowledge/useKnowledgeApi'

const fileInput = ref<HTMLInputElement | null>(null)
const uploadAreaRef = ref<InstanceType<typeof KbUploadArea> | null>(null)

const {
  knowledgeBases, selectedKB, documents, showCreateDialog, newKBName,
  isDragging, uploadTasks, searchQuery, searchResults, isSearching, searchError,
  getStatusText, getDocStatusText,
  selectKnowledgeBase, createKnowledgeBase, deleteKnowledgeBase, deleteDocument,
  handleFileSelect, handleDrop, performSearch,
} = useKnowledgeApi(fileInput)

function triggerUploadFileInput() {
  uploadAreaRef.value?.fileInputRef?.click()
}
</script>

<style scoped src="./KnowledgeView.css"></style>
