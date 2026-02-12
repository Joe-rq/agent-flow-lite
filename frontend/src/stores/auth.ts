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
  const isHydrating = ref(false)

  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function login(email: string, password: string): Promise<void> {
    const response = await axios.post('/api/v1/auth/login', { email, password })
    const { token: newToken, user: userData } = response.data

    token.value = newToken
    user.value = userData
    localStorage.setItem('auth_token', newToken)
  }

  async function register(email: string, password: string): Promise<void> {
    const response = await axios.post('/api/v1/auth/register', { email, password })
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

  async function init(): Promise<boolean> {
    const storedToken = localStorage.getItem('auth_token')
    if (!storedToken) {
      return false
    }

    token.value = storedToken

    if (user.value) {
      return true
    }

    isHydrating.value = true
    try {
      const response = await axios.get('/api/v1/auth/me')
      user.value = response.data
      isHydrating.value = false
      return true
    } catch (error) {
      isHydrating.value = false
      const axiosError = error as { response?: { status?: number } }
      if (axiosError.response?.status === 401) {
        clearAuth()
        return false
      }
      console.error('Failed to fetch user profile:', error)
      return false
    }
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
    isHydrating,
    isAuthenticated,
    isAdmin,
    login,
    register,
    logout,
    init,
    setUser,
    clearAuth,
  }
})
