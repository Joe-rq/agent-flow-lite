<template>
  <div>
    <!-- 上传区域 -->
    <div
      class="upload-area"
      :class="{ dragging: isDragging }"
      @dragenter.prevent="$emit('update:isDragging', true)"
      @dragleave.prevent="$emit('update:isDragging', false)"
      @dragover.prevent
      @drop.prevent="$emit('drop', $event)"
      @click="$emit('trigger-file-input')"
    >
      <input
        ref="fileInputRef"
        type="file"
        accept=".txt,.md"
        multiple
        style="display: none"
        @change="$emit('file-select', $event)"
      />
      <div class="upload-content">
        <div class="upload-icon">📄</div>
        <p class="upload-text">
          <span class="highlight">点击选择文件</span> 或拖拽文件到此处
        </p>
        <p class="upload-hint">支持 .txt, .md 格式</p>
      </div>
    </div>

    <!-- 上传进度列表 -->
    <div v-if="uploadTasks.length > 0" class="upload-tasks">
      <h3>上传进度</h3>
      <div
        v-for="task in uploadTasks"
        :key="task.id"
        class="upload-task-item"
        :class="task.status"
      >
        <div class="task-info">
          <span class="task-name">{{ task.fileName }}</span>
          <span class="task-size">{{ formatFileSize(task.fileSize) }}</span>
        </div>
        <div class="task-progress">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: task.progress + '%' }"></div>
          </div>
          <span class="task-status">{{ getStatusText(task.status) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { formatFileSize } from '@/utils/format'
import type { UploadTask } from '@/types'

const props = defineProps<{
  isDragging: boolean
  uploadTasks: UploadTask[]
  getStatusText: (status: UploadTask['status']) => string
}>()

defineEmits<{
  'trigger-file-input': []
  'drop': [event: DragEvent]
  'file-select': [event: Event]
  'update:isDragging': [value: boolean]
}>()

const fileInputRef = ref<HTMLInputElement | null>(null)

defineExpose({ fileInputRef })
</script>

<style scoped src="./KbUploadArea.css"></style>
