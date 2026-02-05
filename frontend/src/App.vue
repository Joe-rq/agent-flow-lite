<script setup lang="ts">
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import Button from '@/components/ui/Button.vue'

const sidebarCollapsed = ref(false)
const { meta } = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const showChrome = computed(() => !meta.hideChrome && authStore.isAuthenticated)

onMounted(() => {
  const saved = localStorage.getItem('sidebar-collapsed')
  if (saved !== null) {
    sidebarCollapsed.value = saved === 'true'
  }
})

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('sidebar-collapsed', String(sidebarCollapsed.value))
}

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="app-container">
    <header v-if="showChrome" class="app-header">
      <div class="logo">Agent Flow</div>
      <Button
        v-if="authStore.isAuthenticated"
        variant="secondary"
        size="sm"
        @click="handleLogout"
      >
        退出登录
      </Button>
    </header>

    <div class="app-body">
      <aside v-if="showChrome" class="app-sidebar" :class="{ collapsed: sidebarCollapsed }">
        <button class="sidebar-toggle" @click="toggleSidebar" :title="sidebarCollapsed ? '展开侧边栏' : '折叠侧边栏'">
          <span class="toggle-icon">{{ sidebarCollapsed ? '→' : '←' }}</span>
        </button>
        <nav>
          <RouterLink to="/" :title="sidebarCollapsed ? '首页' : ''">
            <span class="nav-icon">🏠</span>
            <span class="nav-text">首页</span>
          </RouterLink>
          <RouterLink to="/workflow" :title="sidebarCollapsed ? '工作流' : ''">
            <span class="nav-icon">⚡</span>
            <span class="nav-text">工作流</span>
          </RouterLink>
          <RouterLink to="/knowledge" :title="sidebarCollapsed ? '知识库' : ''">
            <span class="nav-icon">📚</span>
            <span class="nav-text">知识库</span>
          </RouterLink>
          <RouterLink to="/chat" :title="sidebarCollapsed ? '对话' : ''">
            <span class="nav-icon">💬</span>
            <span class="nav-text">对话</span>
          </RouterLink>
          <RouterLink to="/skills" :title="sidebarCollapsed ? '技能管理' : ''">
            <span class="nav-icon">🧩</span>
            <span class="nav-text">技能管理</span>
          </RouterLink>
          <RouterLink
            v-if="authStore.isAdmin"
            to="/admin"
            :title="sidebarCollapsed ? '管理' : ''"
          >
            <span class="nav-icon">⚙️</span>
            <span class="nav-text">管理</span>
          </RouterLink>
        </nav>
      </aside>

      <main class="app-main">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background-color: var(--bg-primary);
  color: var(--text-primary);
}
</style>

<style scoped>
@import '@/styles/theme.css';

.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-primary);
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 60px;
  background-color: var(--bg-secondary);
  border-bottom: 1px solid var(--border-primary);
}

.logo {
  font-size: 1.2rem;
  font-weight: bold;
  color: var(--text-primary);
}

.app-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.app-sidebar {
  width: 240px;
  padding: 20px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-primary);
  transition: width 300ms ease;
  display: flex;
  flex-direction: column;
  position: relative;
}

.app-sidebar.collapsed {
  width: 60px;
  padding: 20px 10px;
}

.sidebar-toggle {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: var(--radius-sm);
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-base);
  z-index: 10;
}

.sidebar-toggle:hover {
  background-color: var(--accent-cyan-soft);
  color: var(--accent-cyan);
}

.toggle-icon {
  font-size: 14px;
  line-height: 1;
}

.app-sidebar.collapsed .sidebar-toggle {
  right: 50%;
  transform: translateX(50%);
}

.app-sidebar nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 40px;
}

.app-sidebar a {
  color: var(--text-secondary);
  text-decoration: none;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  transition: all var(--transition-base);
  display: flex;
  align-items: center;
  gap: 10px;
  overflow: hidden;
  white-space: nowrap;
}

.app-sidebar a:hover {
  color: var(--text-primary);
  background-color: var(--accent-cyan-soft);
}

.app-sidebar a.router-link-active {
  color: var(--accent-cyan);
  background-color: var(--accent-cyan-soft);
  box-shadow: 0 0 15px var(--accent-cyan-glow);
}

.nav-icon {
  font-size: 18px;
  flex-shrink: 0;
  width: 24px;
  text-align: center;
}

.nav-text {
  transition: opacity 300ms ease, width 300ms ease;
  opacity: 1;
}

.app-sidebar.collapsed .nav-text {
  opacity: 0;
  width: 0;
  overflow: hidden;
}

.app-sidebar.collapsed a {
  padding: 12px;
  justify-content: center;
}

.app-sidebar.collapsed .nav-icon {
  width: auto;
}

.app-main {
  flex: 1;
  padding: 0;
  overflow: hidden;
  background-color: var(--bg-primary);
}
</style>
