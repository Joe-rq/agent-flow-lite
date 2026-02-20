<template>
  <div class="admin-users-view">
    <div class="page-header">
      <h1>用户管理</h1>
      <div class="header-actions">
        <div class="search-box">
          <TextInput
            v-model="searchQuery"
            type="text"
            placeholder="搜索用户邮箱..."
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
import { onMounted } from 'vue'
import Button from '@/components/ui/Button.vue'
import { TextInput } from '@/components/ui'
import { formatDate } from '@/utils/format'
import { useUserAdmin } from '@/composables/useUserAdmin'

const {
  users,
  searchQuery,
  isLoading,
  showConfirmDialog,
  confirmDialogTitle,
  confirmDialogMessage,
  confirmDialogVariant,
  filteredUsers,
  getRoleText,
  isCurrentUser,
  loadCurrentUser,
  loadUsers,
  refreshUsers,
  performSearch,
  toggleUserStatus,
  deleteUser,
  cancelAction,
  executeConfirmedAction,
} = useUserAdmin()

onMounted(async () => {
  await loadCurrentUser()
  await loadUsers()
})
</script>

<style scoped src="./AdminUsersView.css"></style>
