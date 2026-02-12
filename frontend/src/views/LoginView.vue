<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Button from '@/components/ui/Button.vue'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const isLoading = ref(false)
const error = ref('')
const isRegisterMode = ref(false)

async function handleSubmit() {
  error.value = ''

  if (!email.value.trim()) {
    error.value = '请输入邮箱地址'
    return
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email.value.trim())) {
    error.value = '请输入有效的邮箱地址'
    return
  }

  if (!password.value) {
    error.value = '请输入密码'
    return
  }

  if (isRegisterMode.value) {
    if (password.value.length < 6) {
      error.value = '密码至少需要 6 个字符'
      return
    }
    if (password.value !== confirmPassword.value) {
      error.value = '两次输入的密码不一致'
      return
    }
  }

  isLoading.value = true

  try {
    if (isRegisterMode.value) {
      await authStore.register(email.value.trim(), password.value)
    } else {
      await authStore.login(email.value.trim(), password.value)
    }
    router.push('/')
  } catch (err) {
    const errorObj = err as { response?: { data?: { detail?: string } } }
    error.value = errorObj.response?.data?.detail || (isRegisterMode.value ? '注册失败，请重试' : '登录失败，请重试')
  } finally {
    isLoading.value = false
  }
}

function toggleMode() {
  isRegisterMode.value = !isRegisterMode.value
  error.value = ''
  password.value = ''
  confirmPassword.value = ''
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
            @keydown.enter="handleSubmit"
          />
        </div>

        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="请输入密码"
            :disabled="isLoading"
            @keydown.enter="handleSubmit"
          />
        </div>

        <div v-if="isRegisterMode" class="form-group">
          <label for="confirmPassword">确认密码</label>
          <input
            id="confirmPassword"
            v-model="confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            :disabled="isLoading"
            @keydown.enter="handleSubmit"
          />
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <Button
          variant="primary"
          size="lg"
          :disabled="isLoading"
          @click="handleSubmit"
        >
          {{ isLoading ? (isRegisterMode ? '注册中...' : '登录中...') : (isRegisterMode ? '注册' : '登录') }}
        </Button>
      </div>

      <div class="login-footer">
        <p>
          {{ isRegisterMode ? '已有账号？' : '没有账号？' }}
          <a href="#" class="toggle-link" @click.prevent="toggleMode">
            {{ isRegisterMode ? '去登录' : '去注册' }}
          </a>
        </p>
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

.toggle-link {
  color: var(--accent-cyan);
  text-decoration: none;
  font-weight: 500;
}

.toggle-link:hover {
  text-decoration: underline;
}
</style>
