<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="app-container">
    <header class="app-header">
      <div class="logo">Agent Flow</div>
      <nav class="header-nav">
        <RouterLink to="/">首页</RouterLink>
        <RouterLink to="/workflow">工作流</RouterLink>
        <RouterLink to="/knowledge">知识库</RouterLink>
        <RouterLink to="/chat">对话</RouterLink>
      </nav>
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
}
</style>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 60px;
  background-color: #2c3e50;
  color: white;
}

.logo {
  font-size: 1.2rem;
  font-weight: bold;
}

.header-nav {
  display: flex;
  gap: 20px;
}

.header-nav a {
  color: white;
  text-decoration: none;
  padding: 5px 10px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.header-nav a:hover,
.header-nav a.router-link-active {
  background-color: rgba(255, 255, 255, 0.1);
}

.app-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.app-sidebar {
  width: 200px;
  background-color: #f8f9fa;
  border-right: 1px solid #e9ecef;
  padding: 20px;
}

.app-sidebar nav {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.app-sidebar a {
  color: #495057;
  text-decoration: none;
  padding: 10px 15px;
  border-radius: 6px;
  transition: all 0.2s;
}

.app-sidebar a:hover {
  background-color: #e9ecef;
}

.app-sidebar a.router-link-active {
  background-color: #2c3e50;
  color: white;
}

.app-main {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: #fff;
}
</style>
