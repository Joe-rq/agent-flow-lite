import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

let isHydrating = true

export function setHydrated() {
  isHydrating = false
}

export function setupAxiosInterceptors() {
  axios.interceptors.request.use(
    (config) => {
      const authStore = useAuthStore()
      if (authStore.token) {
        config.headers.Authorization = `Bearer ${authStore.token}`
      }
      return config
    },
    (error) => Promise.reject(error)
  )

  axios.interceptors.response.use(
    (response) => response,
    async (error) => {
      if (error.response?.status === 401 && !isHydrating) {
        const authStore = useAuthStore()
        authStore.clearAuth()
        const { default: router } = await import('@/router')
        router.push('/login')
      }
      return Promise.reject(error)
    }
  )
}
