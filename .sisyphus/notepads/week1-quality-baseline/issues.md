# Week 1 Quality Baseline - Issues

## 2026-02-07: P0 Test Failure Report

### Fixed Issues

#### Issue 1: Missing Auth State in Chrome Visibility Tests
**Severity**: P0
**Status**: Fixed
**Files**: `frontend/src/__tests__/auth/login.spec.ts`

**Description**: 
测试 `should show header on non-login routes` 和 `should show sidebar on non-login routes` 失败，因为未设置认证状态。

**Root Cause**: 
App.vue 的 `showChrome` 计算属性要求 `authStore.isAuthenticated` 为 true，但测试中 authStore 初始状态为未认证。

**Fix**:
```typescript
// Set up authenticated state
const authStore = useAuthStore()
authStore.token = 'test-token'
authStore.setUser({ id: 1, email: 'test@example.com', role: 'user', is_active: true, created_at: '2024-01-01' })
```

### Potential Flaky Patterns (Not Found in Current Code)

Checked for but not found:
- ❌ Magic `setTimeout` without `vi.useFakeTimers()`
- ❌ 悬空 Promise 没有 await
- ❌ 非确定性的等待模式

### Non-Issue: Console Errors in Tests

**Observation**: 以下测试输出 console error 但测试本身通过：
- `Auth Store > should set isHydrating to false even when /me fails`
- `Refresh-Logout Bug > network failure during /me should gracefully handle without breaking`

**Analysis**: 这些 error 是测试预期的行为（模拟网络错误），auth store 的 `init()` 函数通过 `console.error` 输出错误信息。这是预期行为，不是 flaky 测试。

**Console Error Location**: `auth.ts:67`
```typescript
console.error('Failed to fetch user profile:', error)
```

### Non-Issue: Vue Router Warnings

**Observation**: `[Vue Router warn]: No match found for location with path "/xxx"`

**Analysis**: 测试路由配置只包含 `/login` 和 `/`，而 App.vue 的 sidebar 包含到 `/workflow`, `/knowledge`, `/chat`, `/skills` 的链接。这些警告不影响测试执行，只是测试配置不完整。

**Mitigation**: 如需消除警告，可在测试路由中添加这些路由定义。

