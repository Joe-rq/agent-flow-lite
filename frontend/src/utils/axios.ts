import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

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
    (error) => {
      if (error.response?.status === 401) {
        const authStore = useAuthStore()
        authStore.clearAuth()
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }
  )
}
