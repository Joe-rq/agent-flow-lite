import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/workflow',
      name: 'workflow',
      component: () => import('../views/WorkflowEditor.vue'),
    },
    {
      path: '/knowledge',
      name: 'knowledge',
      component: () => import('../views/KnowledgeView.vue'),
    },
    {
      path: '/chat',
      name: 'chat',
      component: () => import('../views/ChatTerminal.vue'),
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('../views/AdminUsersView.vue'),
      meta: { requiresAdmin: true },
    },
    {
      path: '/skills',
      name: 'skills',
      component: () => import('../views/SkillsView.vue'),
    },
    {
      path: '/skills/:name',
      name: 'skill-edit',
      component: () => import('../views/SkillEditor.vue'),
    },
  ],
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.public && authStore.isAuthenticated) {
    next('/')
    return
  }

  if (!to.meta.public && !authStore.isAuthenticated) {
    next('/login')
    return
  }

  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next('/')
    return
  }

  next()
})

export default router
