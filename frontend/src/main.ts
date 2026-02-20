import './app.css'
import './assets/main.css'
import './styles/animations.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'
import { setupAxiosInterceptors, setHydrated } from './utils/axios'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)

const authStore = useAuthStore()
setupAxiosInterceptors()
await authStore.init()
setHydrated()

app.use(router)

if (router.currentRoute.value.meta.public && authStore.isAuthenticated) {
  await router.replace('/')
}

app.mount('#app')
