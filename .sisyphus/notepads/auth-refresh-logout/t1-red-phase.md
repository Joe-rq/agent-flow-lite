# Task 1: RED PHASE - Failing Tests for Refresh-Logout Bug

## Date: 2026-02-06

## Summary
Added failing tests that demonstrate the refresh-logout bug in the auth store.

## Bug Description
**Root Cause**: `isAuthenticated` requires BOTH token AND user, but `init()` only restores token from localStorage.

**Impact**: After page refresh, user is logged out even with valid token because:
1. `init()` restores token from localStorage
2. `user` remains `null`
3. `isAuthenticated = !!token && !!user = true && false = false`
4. Router redirects to /login

## Tests Added
Location: `frontend/src/__tests__/auth/login.spec.ts`

### 1. `init with cached token should restore both token and user for isAuthenticated=true`
- **Status**: FAILING
- **Assertion**: `expect(authStore.user).not.toBeNull()`
- **Failure**: `expected null not to be null`
- **Why it fails**: `init()` only restores token, not user

### 2. `refresh with valid token but missing user should trigger revalidation via /api/v1/auth/me`
- **Status**: FAILING
- **Assertion**: `expect(axios.get).toHaveBeenCalledWith('/api/v1/auth/me')`
- **Failure**: `Expected "spy" to be called with arguments: [ '/api/v1/auth/me' ], Number of calls: 0`
- **Why it fails**: `init()` doesn't call `/api/v1/auth/me` to fetch user

### 3. `401 from /me should clear auth state and redirect to /login`
- **Status**: FAILING
- **Assertion**: `expect(authStore.token).toBeNull()`
- **Failure**: `expected 'expired-token' to be null`
- **Why it fails**: `init()` doesn't handle `/me` endpoint errors

### 4. `network failure during /me should gracefully handle without breaking`
- **Status**: FAILING
- **Assertion**: `expect(axios.get).toHaveBeenCalledWith('/api/v1/auth/me')`
- **Failure**: `Expected "spy" to be called with arguments: [ '/api/v1/auth/me' ], Number of calls: 0`
- **Why it fails**: `init()` never attempts to fetch `/me`

### 5. `isAuthenticated should be false when token exists but user is null` (DOCUMENTATION)
- **Status**: PASSING
- **Purpose**: Documents the current buggy behavior

### 6. `should restore user from localStorage if cached during init` (DOCUMENTATION)
- **Status**: PASSING
- **Purpose**: Confirms current implementation doesn't cache user

## Test Results
```
28 tests total
- 22 passed (existing tests + documentation tests)
- 6 failed
  - 4 from Refresh-Logout Bug (expected failures - prove the bug)
  - 2 from App Chrome Hiding (pre-existing failures, unrelated)
```

## Evidence
Full vitest output saved to: `.sisyphus/evidence/task-1-red-vitest.txt`

## Required Fix (for GREEN phase)
The `init()` function needs to:
1. Restore token from localStorage (already done)
2. Fetch user data from `/api/v1/auth/me` if token exists but user is null
3. Handle 401 responses by clearing auth state
4. Handle network failures gracefully without breaking

## Files Modified
- `frontend/src/__tests__/auth/login.spec.ts` - Added 6 new tests in "Refresh-Logout Bug (RED PHASE)" describe block
