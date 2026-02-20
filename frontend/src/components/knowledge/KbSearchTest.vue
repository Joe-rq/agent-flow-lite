<template>
  <div class="search-section">
    <h3>检索测试</h3>
    <div class="search-box">
      <input
        :value="searchQuery"
        type="text"
        placeholder="输入查询内容测试检索效果..."
        class="search-input"
        @input="$emit('update:searchQuery', ($event.target as HTMLInputElement).value)"
        @keyup.enter="$emit('search')"
      />
      <Button
        variant="default"
        :disabled="!searchQuery.trim() || isSearching"
        @click="$emit('search')"
      >
        {{ isSearching ? '检索中...' : '检索' }}
      </Button>
    </div>

    <div v-if="searchResults.length > 0" class="search-results">
      <div class="results-header">
        <span>找到 {{ searchResults.length }} 个相关片段</span>
      </div>
      <div
        v-for="(result, index) in searchResults"
        :key="index"
        class="result-item"
      >
        <div class="result-meta">
          <span class="result-index">#{{ index + 1 }}</span>
          <span class="result-score">相似度: {{ (result.score * 100).toFixed(1) }}%</span>
        </div>
        <div class="result-text">{{ result.text }}</div>
      </div>
    </div>

    <div v-if="searchError" class="search-error">
      {{ searchError }}
    </div>
  </div>
</template>

<script setup lang="ts">
import Button from '@/components/ui/Button.vue'
import type { SearchResult } from '@/types'

defineProps<{
  searchQuery: string
  searchResults: SearchResult[]
  isSearching: boolean
  searchError: string
}>()

defineEmits<{
  'update:searchQuery': [value: string]
  search: []
}>()
</script>

<style scoped src="./KbSearchTest.css"></style>
