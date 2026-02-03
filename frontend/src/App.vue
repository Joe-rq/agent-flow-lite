<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="app-container">
    <header class="app-header">
      <div class="logo">Agent Flow</div>
    </header>

    <div class="app-body">
      <aside class="app-sidebar">
        <nav>
          <RouterLink to="/">首页</RouterLink>
          <RouterLink to="/workflow">工作流</RouterLink>
          <RouterLink to="/knowledge">知识库</RouterLink>
          <RouterLink to="/chat">对话</RouterLink>
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
  /* Glassmorphism effect */
  background: rgba(18, 18, 26, 0.6);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-right: 1px solid var(--border-primary);
}

/* Fallback for browsers without backdrop-filter support */
@supports not ((backdrop-filter: blur(20px)) or (-webkit-backdrop-filter: blur(20px))) {
  .app-sidebar {
    background: var(--bg-secondary);
  }
}

.app-sidebar nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
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

.app-main {
  flex: 1;
  padding: 0;
  overflow: hidden;
  background-color: var(--bg-primary);
}
</style>
