<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Button from '@/components/ui/Button.vue'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const isLoading = ref(false)
const error = ref('')

async function handleLogin() {
  if (!email.value.trim()) {
    error.value = '请输入邮箱地址'
    return
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email.value.trim())) {
    error.value = '请输入有效的邮箱地址'
    return
  }

  isLoading.value = true
  error.value = ''

  try {
    await authStore.login(email.value.trim())
    router.push('/')
  } catch (err) {
    const errorObj = err as { response?: { data?: { detail?: string } } }
    error.value = errorObj.response?.data?.detail || '登录失败，请重试'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="login-view">
    <div class="login-container">
      <div class="login-header">
        <h1>Agent Flow</h1>
        <p>智能体编排平台</p>
      </div>

      <div class="login-form">
        <div class="form-group">
          <label for="email">邮箱地址</label>
          <input
            id="email"
            v-model="email"
            type="email"
            placeholder="请输入邮箱地址"
            :disabled="isLoading"
            @keydown.enter="handleLogin"
          />
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <Button
          variant="primary"
          size="lg"
          :disabled="isLoading"
          @click="handleLogin"
        >
          {{ isLoading ? '登录中...' : '登录 / 注册' }}
        </Button>
      </div>

      <div class="login-footer">
        <p>输入邮箱即可开始使用</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-view {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-tertiary) 100%);
  padding: var(--space-lg);
}

.login-container {
  width: 100%;
  max-width: 400px;
  background: var(--surface-primary);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  padding: var(--space-2xl);
}

.login-header {
  text-align: center;
  margin-bottom: var(--space-xl);
}

.login-header h1 {
  font-size: var(--text-3xl);
  font-weight: 700;
  background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 var(--space-sm) 0;
}

.login-header p {
  color: var(--text-secondary);
  font-size: var(--text-base);
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.login-form .btn {
  width: 100%;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.form-group label {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-primary);
}

.form-group input {
  padding: var(--space-md);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.form-group input:focus {
  outline: none;
  border-color: var(--accent-cyan);
  box-shadow: 0 0 0 3px var(--accent-cyan-soft);
}

.form-group input:disabled {
  background: var(--bg-tertiary);
  cursor: not-allowed;
  opacity: 0.6;
}

.error-message {
  padding: var(--space-sm) var(--space-md);
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: var(--radius-md);
  color: #dc2626;
  font-size: var(--text-sm);
}

.login-footer {
  text-align: center;
  margin-top: var(--space-xl);
  padding-top: var(--space-lg);
  border-top: 1px solid var(--border-secondary);
}

.login-footer p {
  color: var(--text-muted);
  font-size: var(--text-sm);
  margin: 0;
}
</style>
