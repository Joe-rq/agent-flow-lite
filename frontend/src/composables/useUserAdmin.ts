import { ref, computed } from 'vue'
import axios from 'axios'
import { API_BASE } from '@/utils/constants'
import { useToast } from '@/composables/useToast'
import type { User } from '@/types'

export function useUserAdmin() {
  const users = ref<User[]>([])
  const searchQuery = ref('')
  const isLoading = ref(false)
  const currentUser = ref<User | null>(null)

  const { showToast } = useToast()

  // Confirm dialog state
  const showConfirmDialog = ref(false)
  const confirmDialogTitle = ref('')
  const confirmDialogMessage = ref('')
  const confirmDialogVariant = ref<'primary' | 'secondary' | 'danger'>('primary')
  const pendingAction = ref<(() => Promise<void>) | null>(null)

  const filteredUsers = computed(() => {
    if (!searchQuery.value.trim()) return users.value
    const query = searchQuery.value.toLowerCase().trim()
    return users.value.filter((user) => user.email.toLowerCase().includes(query))
  })

  function getRoleText(role: string): string {
    return role === 'admin' ? '管理员' : '用户'
  }

  function isCurrentUser(user: User): boolean {
    return currentUser.value?.id === user.id
  }

  function showError(message: string) {
    showToast(message)
  }

  async function loadCurrentUser() {
    try {
      const response = await axios.get(`${API_BASE}/auth/me`)
      currentUser.value = response.data
    } catch (error) {
      console.error('加载当前用户信息失败:', error)
    }
  }

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

  async function refreshUsers() {
    searchQuery.value = ''
    await loadUsers()
  }

  function performSearch() {
    // Search is client-side filtered via computed
  }

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

  function cancelAction() {
    showConfirmDialog.value = false
    pendingAction.value = null
  }

  async function executeConfirmedAction() {
    if (!pendingAction.value) return
    isLoading.value = true
    try {
      await pendingAction.value()
    } finally {
      isLoading.value = false
      showConfirmDialog.value = false
      pendingAction.value = null
    }
  }

  return {
    users,
    searchQuery,
    isLoading,
    currentUser,
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
  }
}
