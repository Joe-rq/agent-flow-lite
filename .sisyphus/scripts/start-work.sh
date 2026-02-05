#!/usr/bin/env bash

# Start-work execution script

PLAN_FILE=".sisyphus/plans/login-page-cleanup.md"
WORK_DIR="/Users/qrq/Documents/code/05-web-projects/ agent-flow-lite"
LOG_DIR="$WORK_DIR/.sisyphus/logs"
TIMESTAMP=$(date +%Y%m%d%H%M%S)

echo "[$TIMESTAMP] Starting work session..."
echo "Plan: $PLAN_FILE"

# Task 1: Add TDD tests (RED)
echo "[$TIMESTAMP] Task 1: Creating test file..."

TEST_FILE="$WORK_DIR/frontend/src/__tests__/App.spec.ts"

# Check if test file exists
if [ ! -f "$TEST_FILE" ]; then
  echo "[$TIMESTAMP] Creating test directory..."
  mkdir -p "$WORK_DIR/frontend/src/__tests__"
fi

# Write test file
cat > "$TEST_FILE" << 'EOF'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import App from '@/App.vue'

describe('App Chrome and Navigation', () => {
  let router: ReturnType<typeof createRouter>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(async () => {
    router = createRouter({
      history: createWebHistory(),
      routes: [
        {
          path: '/login',
          name: 'login',
          component: { template: '<div>Login</div>' },
          meta: { public: true, hideChrome: true },
        },
        {
          path: '/',
          name: 'home',
          component: { template: '<div>Home</div>' },
        },
      ],
    })
    pinia = createPinia()
    setActivePinia(pinia)
    await router.push('/login')
    await router.isReady()
    vi.clearAllMocks()
  })

  it('should NOT render header when user is not authenticated', async () => {
    const authStore = useAuthStore()
    authStore.token = null
    authStore.user = null

    const wrapper = mount(App, {
      global: {
        plugins: [router, pinia],
      },
    })

    const header = wrapper.find('.app-header')
    expect(header.exists()).toBe(false)
  })

  it('should NOT render sidebar when user is not authenticated', async () => {
    const authStore = useAuthStore()
    authStore.token = null
    authStore.user = null

    const wrapper = mount(App, {
      global: {
        plugins: [router, pinia],
      },
    })

    const sidebar = wrapper.find('.app-sidebar')
    expect(sidebar.exists()).toBe(false)
  })

  it('should render header when user is authenticated', async () => {
    const authStore = useAuthStore()
    authStore.token = 'test-token'
    authStore.setUser({ id: 1, email: 'test@example.com', role: 'user' })

    const wrapper = mount(App, {
      global: {
        plugins: [router, pinia],
      },
    })

    const header = wrapper.find('.app-header')
    expect(header.exists()).toBe(true)
  })

  it('should render sidebar when user is authenticated', async () => {
    const authStore = useAuthStore()
    authStore.token = 'test-token'
    authStore.setUser({ id: 1, email: 'test@example.com', role: 'user' })

    const wrapper = mount(App, {
      global: {
        plugins: [router, pinia],
      },
    })

    const sidebar = wrapper.find('.app-sidebar')
    expect(sidebar.exists()).toBe(true)
  })

  it('should redirect to /login immediately after clicking logout', async () => {
    const authStore = useAuthStore()
    authStore.token = 'test-token'
    authStore.setUser({ id: 1, email: 'test@example.com', role: 'user' })

    vi.mocked(axios, 'post').mockResolvedValueOnce({ data: {} })

    const wrapper = mount(App, {
      global: {
        plugins: [router, pinia],
      },
    })

    const logoutButton = wrapper.find('button')
    if (logoutButton) {
      await logoutButton.trigger('click')
    }

    await new Promise(resolve => setTimeout(resolve, 10))

    expect(router.currentRoute.value.path).toBe('/login')
  })
})
EOF

echo "[$TIMESTAMP] Test file created/updated"
echo "[$TIMESTAMP] Task 1 completed"

# Task 2: Update App.vue logic
echo "[$TIMESTAMP] Task 2: Updating App.vue to fix chrome display and logout redirect..."

APP_FILE="$WORK_DIR/frontend/src/App.vue"

# Read existing App.vue
if [ -f "$APP_FILE" ]; then
  echo "[$TIMESTAMP] Backing up App.vue..."
  cp "$APP_FILE" "$APP_FILE.bak"
fi

# Apply changes
# Line 11: const showChrome = computed(() => !meta.hideChrome)
sed -i '' '11s/const showChrome = computed(() =>/const showChrome = computed(() => !meta.hideChrome \&\& !authStore.isAuthenticated)/' "$APP_FILE"

# Line 25-27: async function handleLogout() { await authStore.logout() }
sed -i '' '25,27s/async function handleLogout() {/async function handleLogout() {\n  await authStore.logout()\n  router.push("\/login")\n}/' "$APP_FILE"

echo "[$TIMESTAMP] App.vue updated"
echo "[$TIMESTAMP] Task 2 completed"

# Run tests
echo "[$TIMESTAMP] Running tests..."
cd "$WORK_DIR/frontend" && npm run test -- src/__tests__/App.spec.ts

echo "[$TIMESTAMP] Work session completed"