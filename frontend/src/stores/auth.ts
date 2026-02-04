import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'

export interface User {
  id: number
  email: string
  role: 'admin' | 'user'
  is_active: boolean
  created_at: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(null)
  const user = ref<User | null>(null)

  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function login(email: string): Promise<void> {
    const response = await axios.post('/api/v1/auth/login', { email })
    const { token: newToken, user: userData } = response.data

    token.value = newToken
    user.value = userData
    localStorage.setItem('auth_token', newToken)
  }

  async function logout(): Promise<void> {
    try {
      await axios.post('/api/v1/auth/logout')
    } catch {
      console.error('Logout API failed')
    }

    token.value = null
    user.value = null
    localStorage.removeItem('auth_token')
  }

  function init(): boolean {
    const storedToken = localStorage.getItem('auth_token')
    if (storedToken) {
      token.value = storedToken
      return true
    }
    return false
  }

  function setUser(userData: User): void {
    user.value = userData
  }

  function clearAuth(): void {
    token.value = null
    user.value = null
    localStorage.removeItem('auth_token')
  }

  return {
    token,
    user,
    isAuthenticated,
    isAdmin,
    login,
    logout,
    init,
    setUser,
    clearAuth,
  }
})
