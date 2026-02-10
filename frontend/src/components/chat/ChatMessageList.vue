<template>
  <div ref="containerRef" class="messages-container">
    <div
      v-for="(message, index) in currentMessages"
      :key="index"
      class="message-wrapper"
      :class="message.role"
    >
      <div class="message-avatar">
        {{ message.role === 'user' ? '\uD83D\uDC64' : '\uD83E\uDD16' }}
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
            @click="$emit('open-citation', citation)"
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
      <button class="citation-close" @click="$emit('close-citation')">×</button>
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
</template>

<script setup lang="ts">
import { ref, type Ref } from 'vue'
import type { Message, CitationSource } from '@/composables/chat/types'

defineProps<{
  currentMessages: Message[]
  currentThought: string
  activeCitation: CitationSource | null
}>()

defineEmits<{
  'open-citation': [source: CitationSource]
  'close-citation': []
}>()

const containerRef = ref<HTMLElement | null>(null)

defineExpose({
  containerRef,
})

function getContainerRef(): Ref<HTMLElement | null> {
  return containerRef
}
</script>

<style scoped src="./ChatMessageList.css"></style>
