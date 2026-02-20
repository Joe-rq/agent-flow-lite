<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <Button class="new-chat-btn" variant="default" @click="$emit('create-session')">
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
        @click="$emit('switch-session', session.id)"
      >
        <div class="session-info">
          <div class="session-title">{{ session.title }}</div>
          <div class="session-time">{{ formatTime(session.updatedAt) }}</div>
        </div>
        <button
          class="session-delete-btn"
          @click.stop="$emit('delete-session', session.id)"
          title="删除会话"
        >
          ×
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import Button from '@/components/ui/Button.vue'
import type { Session } from '@/composables/chat/types'

defineProps<{
  sessions: Session[]
  currentSessionId: string
}>()

defineEmits<{
  'create-session': []
  'switch-session': [sessionId: string]
  'delete-session': [sessionId: string]
}>()

function formatTime(timestamp: number): string {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<style scoped src="./ChatSidebar.css"></style>
