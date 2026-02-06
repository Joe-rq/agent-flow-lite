<template>
  <div class="admin-users-view">
    <div class="page-header">
      <h1>用户管理</h1>
      <div class="header-actions">
        <div class="search-box">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索用户邮箱..."
            class="search-input"
            @keyup.enter="performSearch"
          />
          <Button variant="secondary" size="sm" @click="performSearch" :disabled="isLoading">
            🔍 搜索
          </Button>
        </div>
        <Button variant="secondary" size="sm" @click="refreshUsers" :disabled="isLoading">
          🔄 刷新
        </Button>
      </div>
    </div>

    <!-- 用户列表 -->
    <div class="users-container">
      <div v-if="isLoading && users.length === 0" class="loading-state">
        <p>加载中...</p>
      </div>

      <div v-else-if="users.length === 0" class="empty-state">
        <p>{{ searchQuery ? '未找到匹配的用户' : '暂无用户' }}</p>
      </div>

      <div v-else class="users-table">
        <div class="table-header">
          <span class="col-email">邮箱</span>
          <span class="col-role">角色</span>
          <span class="col-status">状态</span>
          <span class="col-created">创建时间</span>
          <span class="col-actions">操作</span>
        </div>
        <div v-for="user in filteredUsers" :key="user.id" class="table-row">
          <span class="col-email" :title="user.email">{{ user.email }}</span>
          <span class="col-role">
            <span class="role-badge" :class="user.role">{{ getRoleText(user.role) }}</span>
          </span>
          <span class="col-status">
            <span class="status-badge" :class="user.is_active ? 'active' : 'disabled'">
              {{ user.is_active ? '启用' : '禁用' }}
            </span>
          </span>
          <span class="col-created">{{ formatDate(user.created_at) }}</span>
          <span class="col-actions">
            <template v-if="!isCurrentUser(user)">
              <Button
                variant="secondary"
                size="sm"
                @click="toggleUserStatus(user)"
                :disabled="isLoading"
              >
                {{ user.is_active ? '禁用' : '启用' }}
              </Button>
              <Button
                variant="danger"
                size="sm"
                @click="deleteUser(user)"
                :disabled="isLoading"
              >
                删除
              </Button>
            </template>
            <span v-else class="self-indicator">当前用户</span>
          </span>
        </div>
      </div>
    </div>

    <!-- 确认对话框 -->
    <div v-if="showConfirmDialog" class="dialog-overlay" @click.self="cancelAction">
      <div class="dialog">
        <h3>{{ confirmDialogTitle }}</h3>
        <p class="dialog-message">{{ confirmDialogMessage }}</p>
        <div class="dialog-actions">
          <Button variant="secondary" @click="cancelAction" :disabled="isLoading">
            取消
          </Button>
          <Button
            :variant="confirmDialogVariant"
            @click="executeConfirmedAction"
            :disabled="isLoading"
          >
            {{ isLoading ? '处理中...' : '确认' }}
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import Button from '@/components/ui/Button.vue'

// 类型定义
interface User {
  id: number
  email: string
  role: 'admin' | 'user'
  is_active: boolean
  created_at: string
}

// 状态
const users = ref<User[]>([])
const searchQuery = ref('')
const isLoading = ref(false)
const currentUser = ref<User | null>(null)

// 确认对话框状态
const showConfirmDialog = ref(false)
const confirmDialogTitle = ref('')
const confirmDialogMessage = ref('')
const confirmDialogVariant = ref<'primary' | 'secondary' | 'danger'>('primary')
const pendingAction = ref<(() => Promise<void>) | null>(null)

// API 基础 URL
const API_BASE = '/api/v1'

// 过滤后的用户列表
const filteredUsers = computed(() => {
  if (!searchQuery.value.trim()) {
    return users.value
  }
  const query = searchQuery.value.toLowerCase().trim()
  return users.value.filter(user => user.email.toLowerCase().includes(query))
})

// 格式化日期
function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 获取角色文本
function getRoleText(role: string): string {
  return role === 'admin' ? '管理员' : '用户'
}

// 检查是否为当前用户
function isCurrentUser(user: User): boolean {
  return currentUser.value?.id === user.id
}

// 显示错误提示
function showError(message: string) {
  alert(message)
}

// 加载当前用户信息
async function loadCurrentUser() {
  try {
    const response = await axios.get(`${API_BASE}/auth/me`)
    currentUser.value = response.data
  } catch (error) {
    console.error('加载当前用户信息失败:', error)
  }
}

// 加载用户列表
async function loadUsers() {
  isLoading.value = true
  try {
    const response = await axios.get(`${API_BASE}/admin/users`)
    users.value = response.data.users || []
  } catch (error: any) {
    console.error('加载用户列表失败:', error)
    showError(error.response?.data?.detail || '加载用户列表失败')
  } finally {
    isLoading.value = false
  }
}

// 刷新用户列表
async function refreshUsers() {
  searchQuery.value = ''
  await loadUsers()
}

// 搜索用户
function performSearch() {
  // 搜索在前端过滤，不需要额外请求
  // 如果需要后端搜索，可以在这里调用 API
}

// 切换用户状态
async function toggleUserStatus(user: User) {
  if (isCurrentUser(user)) {
    showError('不能禁用自己')
    return
  }

  const action = user.is_active ? '禁用' : '启用'
  confirmDialogTitle.value = `${action}用户`
  confirmDialogMessage.value = `确定要${action}用户 "${user.email}" 吗？`
  confirmDialogVariant.value = user.is_active ? 'danger' : 'primary'

  pendingAction.value = async () => {
    try {
      const endpoint = user.is_active ? 'disable' : 'enable'
      await axios.post(`${API_BASE}/admin/users/${user.id}/${endpoint}`)
      await loadUsers()
    } catch (error: any) {
      console.error(`${action}用户失败:`, error)
      showError(error.response?.data?.detail || `${action}用户失败`)
    }
  }

  showConfirmDialog.value = true
}

// 删除用户
async function deleteUser(user: User) {
  if (isCurrentUser(user)) {
    showError('不能删除自己')
    return
  }

  confirmDialogTitle.value = '删除用户'
  confirmDialogMessage.value = `确定要删除用户 "${user.email}" 吗？此操作不可恢复。`
  confirmDialogVariant.value = 'danger'

  pendingAction.value = async () => {
    try {
      await axios.delete(`${API_BASE}/admin/users/${user.id}`)
      await loadUsers()
    } catch (error: any) {
      console.error('删除用户失败:', error)
      showError(error.response?.data?.detail || '删除用户失败')
    }
  }

  showConfirmDialog.value = true
}

// 取消操作
function cancelAction() {
  showConfirmDialog.value = false
  pendingAction.value = null
}

// 执行确认的操作
async function executeConfirmedAction() {
  if (pendingAction.value) {
    isLoading.value = true
    try {
      await pendingAction.value()
    } finally {
      isLoading.value = false
      showConfirmDialog.value = false
      pendingAction.value = null
    }
  }
}

// 生命周期
onMounted(async () => {
  await loadCurrentUser()
  await loadUsers()
})
</script>

<style scoped>
.admin-users-view {
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
  color: var(--text-primary);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-box {
  display: flex;
  gap: 8px;
  align-items: center;
}

.search-input {
  padding: 8px 12px;
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  font-size: 14px;
  width: 240px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  transition: border-color var(--transition-fast);
}

.search-input:focus {
  outline: none;
  border-color: var(--accent-cyan);
}

.search-input::placeholder {
  color: var(--text-muted);
}

.users-container {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
  overflow: hidden;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
}

.empty-state p {
  margin: 0;
  font-size: 16px;
}

.users-table {
  display: flex;
  flex-direction: column;
}

.table-header,
.table-row {
  display: grid;
  grid-template-columns: 2fr 100px 100px 160px 180px;
  gap: 16px;
  padding: 14px 20px;
  align-items: center;
}

.table-header {
  background-color: var(--bg-tertiary);
  font-weight: 600;
  color: var(--text-primary);
  font-size: 14px;
  border-bottom: 1px solid var(--border-primary);
}

.table-row {
  border-bottom: 1px solid var(--border-secondary);
  font-size: 14px;
  transition: background-color var(--transition-fast);
}

.table-row:hover {
  background-color: var(--bg-tertiary);
}

.table-row:last-child {
  border-bottom: none;
}

.col-email {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-primary);
}

.col-role,
.col-status {
  display: flex;
}

.role-badge {
  padding: 4px 10px;
  border-radius: var(--radius-full);
  font-size: 12px;
  font-weight: 500;
}

.role-badge.admin {
  background-color: var(--accent-purple-soft);
  color: var(--accent-purple);
}

.role-badge.user {
  background-color: var(--accent-cyan-soft);
  color: var(--accent-cyan);
}

.status-badge {
  padding: 4px 10px;
  border-radius: var(--radius-full);
  font-size: 12px;
  font-weight: 500;
}

.status-badge.active {
  background-color: #dcfce7;
  color: #166534;
}

.status-badge.disabled {
  background-color: #fee2e2;
  color: #991b1b;
}

.col-created {
  color: var(--text-secondary);
  font-size: 13px;
}

.col-actions {
  display: flex;
  gap: 8px;
}

.self-indicator {
  color: var(--text-muted);
  font-size: 13px;
  font-style: italic;
}

/* 对话框 */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--bg-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
}

.dialog {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: 24px;
  width: 400px;
  max-width: 90vw;
  border: 1px solid var(--border-primary);
  box-shadow: var(--shadow-lg);
}

.dialog h3 {
  margin: 0 0 12px 0;
  font-size: 18px;
  color: var(--text-primary);
}

.dialog-message {
  margin: 0 0 20px 0;
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .search-box {
    flex: 1;
    min-width: 200px;
  }

  .search-input {
    width: 100%;
  }

  .table-header,
  .table-row {
    grid-template-columns: 1fr 80px 80px 120px 140px;
    gap: 8px;
    padding: 12px 16px;
  }

  .col-created {
    font-size: 12px;
  }
}
</style>
