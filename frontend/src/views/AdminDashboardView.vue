<template>
  <div class="admin-dashboard-view">
    <div class="page-header">
      <h1>LLM 成本仪表盘</h1>
      <div class="header-actions">
        <div class="time-range-tabs">
          <button
            v-for="range in timeRanges"
            :key="range.value"
            :class="['tab-btn', { active: timeRange === range.value }]"
            @click="setTimeRange(range.value)"
          >
            {{ range.label }}
          </button>
        </div>
        <Button variant="outline" size="sm" @click="fetchTokenUsage" :disabled="isLoading">
          刷新
        </Button>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">总请求数</div>
        <div class="stat-value">{{ formatNumber(data?.total_requests ?? 0) }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">输入 Tokens</div>
        <div class="stat-value">{{ formatNumber(data?.total_input_tokens ?? 0) }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">输出 Tokens</div>
        <div class="stat-value">{{ formatNumber(data?.total_output_tokens ?? 0) }}</div>
      </div>
      <div class="stat-card highlight">
        <div class="stat-label">估算成本</div>
        <div class="stat-value">${{ estimatedCost.toFixed(4) }}</div>
      </div>
    </div>

    <!-- Loading/Error State -->
    <div v-if="isLoading && !data" class="loading-state">
      <p>加载中...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
    </div>

    <!-- Detail Sections -->
    <template v-else-if="data">
      <!-- By Provider -->
      <div class="section">
        <h2>按 Provider 统计</h2>
        <div v-if="providerList.length === 0" class="empty-state">
          <p>暂无数据</p>
        </div>
        <div v-else class="usage-table">
          <div class="table-header">
            <span>Provider</span>
            <span>请求数</span>
            <span>输入 Tokens</span>
            <span>输出 Tokens</span>
            <span>总计</span>
          </div>
          <div v-for="item in providerList" :key="item.name" class="table-row">
            <span class="col-name">{{ item.name }}</span>
            <span>{{ formatNumber(item.requests) }}</span>
            <span>{{ formatNumber(item.input_tokens) }}</span>
            <span>{{ formatNumber(item.output_tokens) }}</span>
            <span>{{ formatNumber(item.total) }}</span>
          </div>
        </div>
      </div>

      <!-- By Model -->
      <div class="section">
        <h2>按 Model 统计</h2>
        <div v-if="modelList.length === 0" class="empty-state">
          <p>暂无数据</p>
        </div>
        <div v-else class="usage-table">
          <div class="table-header">
            <span>Model</span>
            <span>请求数</span>
            <span>输入 Tokens</span>
            <span>输出 Tokens</span>
            <span>总计</span>
          </div>
          <div v-for="item in modelList" :key="item.name" class="table-row">
            <span class="col-name">{{ item.name }}</span>
            <span>{{ formatNumber(item.requests) }}</span>
            <span>{{ formatNumber(item.input_tokens) }}</span>
            <span>{{ formatNumber(item.output_tokens) }}</span>
            <span>{{ formatNumber(item.total) }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import Button from '@/components/ui/Button.vue'
import { useDashboard, type TimeRange } from '@/composables/useDashboard'

const timeRanges: { value: TimeRange; label: string }[] = [
  { value: '24h', label: '24 小时' },
  { value: '7d', label: '7 天' },
  { value: '30d', label: '30 天' },
]

const {
  data,
  timeRange,
  isLoading,
  error,
  estimatedCost,
  providerList,
  modelList,
  fetchTokenUsage,
  setTimeRange,
} = useDashboard()

function formatNumber(num: number): string {
  if (num >= 1_000_000) {
    return (num / 1_000_000).toFixed(2) + 'M'
  }
  if (num >= 1_000) {
    return (num / 1_000).toFixed(1) + 'K'
  }
  return num.toString()
}

onMounted(() => {
  fetchTokenUsage()
})
</script>

<style scoped>
.admin-dashboard-view {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-foreground);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.time-range-tabs {
  display: flex;
  gap: 4px;
  background: var(--color-muted);
  padding: 4px;
  border-radius: var(--radius-md);
}

.tab-btn {
  padding: 6px 12px;
  border: none;
  background: transparent;
  color: var(--color-muted-foreground);
  cursor: pointer;
  border-radius: var(--radius-sm);
  font-size: 13px;
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  color: var(--color-foreground);
}

.tab-btn.active {
  background: var(--color-card);
  color: var(--color-foreground);
  box-shadow: var(--shadow-sm);
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 20px;
}

.stat-card.highlight {
  background: linear-gradient(135deg, var(--color-primary-soft), var(--color-accent-soft));
  border-color: var(--color-primary);
}

.stat-label {
  font-size: 13px;
  color: var(--color-muted-foreground);
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-foreground);
}

/* Sections */
.section {
  margin-bottom: 32px;
}

.section h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-foreground);
  margin: 0 0 16px 0;
}

/* Usage Table */
.usage-table {
  background: var(--color-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  overflow: hidden;
}

.usage-table .table-header,
.usage-table .table-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr;
  gap: 16px;
  padding: 14px 20px;
  align-items: center;
}

.usage-table .table-header {
  background-color: var(--color-muted);
  font-weight: 600;
  color: var(--color-foreground);
  font-size: 13px;
}

.usage-table .table-row {
  border-bottom: 1px solid var(--color-border);
  font-size: 14px;
  color: var(--color-foreground);
}

.usage-table .table-row:last-child {
  border-bottom: none;
}

.col-name {
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* States */
.loading-state,
.error-state,
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--color-muted-foreground);
  background: var(--color-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
}

.error-state {
  color: var(--color-destructive);
}

/* Responsive */
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .usage-table .table-header,
  .usage-table .table-row {
    grid-template-columns: 1.5fr 1fr 1fr 1fr;
    gap: 8px;
    padding: 12px 16px;
    font-size: 13px;
  }

  .usage-table .table-header span:nth-child(5),
  .usage-table .table-row span:nth-child(5) {
    display: none;
  }
}
</style>
