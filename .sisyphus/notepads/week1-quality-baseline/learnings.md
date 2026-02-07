# Week 1 Quality Baseline - Learnings

## Task: 隔离 Playwright 与 Vitest，清理测试收集污染

### 问题分析

1. **Playwright E2E 测试文件**：`frontend/src/__tests__/login-verification.spec.ts`
   - 使用 `@playwright/test` 导入
   - 但 `@playwright/test` 包未安装在项目中

2. **Vitest 配置**：`frontend/vitest.config.ts`
   - 已有正确的 exclude 配置：`['src/__tests__/login-verification.spec.ts', 'node_modules/', 'e2e/']`
   - 这意味着 Vitest 本身不会收集 Playwright 测试文件

3. **E2E 测试命令**：`frontend/package.json`
   - 已有 `test:e2e` 命令：`npx playwright test src/__tests__/login-verification.spec.ts`
   - 但命令因缺少 `@playwright/test` 包而失败

### 解决方案

1. **安装 @playwright/test**：
   ```bash
   cd frontend && npm install --save-dev @playwright/test
   ```

2. **验证 Vitest 配置**：
   - exclude 配置正确，无需修改
   - Vitest 不会收集 Playwright 测试文件

3. **验证结果**：
   - `npm run test -- --run` 成功运行（162 测试通过，2 失败 - 与 Playwright 无关）
   - `npm run test:e2e` 现在可以正常加载测试文件（失败是因为浏览器未安装，不是包问题）

### 关键配置

**frontend/vitest.config.ts**:
```ts
exclude: ['src/__tests__/login-verification.spec.ts', 'node_modules/', 'e2e/']
```

**frontend/package.json**:
```json
{
  "scripts": {
    "test": "vitest",
    "test:e2e": "npx playwright test src/__tests__/login-verification.spec.ts"
  },
  "devDependencies": {
    "@playwright/test": "^1.x.x"
  }
}
```

### 后续建议

1. 如需运行完整 E2E 测试，需执行 `npx playwright install` 安装浏览器
2. 确保 E2E 测试时前端 dev 服务器正在运行
3. 考虑将 E2E 测试文件移动到独立的 `e2e/` 目录，与单元测试完全分离

## 2026-02-07: P0 Test Fix

### Root Cause Analysis

#### Issue: App Chrome Tests Failing
**File**: frontend/src/__tests__/auth/login.spec.ts
**Tests**: 
- App Chrome Hiding on Login > should show header on non-login routes
- App Chrome Hiding on Login > should show sidebar on non-login routes

**Problem**: App.vue 中 showChrome 计算属性需要两个条件：
- !route.meta.hideChrome
- authStore.isAuthenticated

测试只满足了第一个条件（/login 有 hideChrome: true，而 / 没有），但 authStore.isAuthenticated 在测试中是 false（token 和 user 都是 null）。

**Solution**: 在测试中添加认证状态设置

### Testing Best Practices Learned

1. 理解组件的依赖关系: 测试 UI 组件时，必须理解其计算属性依赖的所有状态

2. Pinia Store 在测试中的使用:
   - 使用 setActivePinia(createPinia()) 初始化
   - 可以通过 useAuthStore() 获取实例并直接修改状态
   - isAuthenticated 是计算属性，依赖于 token 和 user

3. Vue Router 警告: [Vue Router warn]: No match found for location with path 是测试路由配置不完整导致的，不影响测试结果但会产生噪音输出

### Verification Results

- Frontend P0: 52 tests × 3 runs = 156/156 passed
- Backend P0: 45 tests × 3 runs = 135/135 passed
- No flaky patterns detected: 无 setTimeout, 无悬空 Promise

---

## 2026-02-07: P1 Issue 闭环建立

### 发现

全量测试通过后，识别出 2 个 P1 级别技术债务：

#### Issue #1: Vue Router 路径未匹配警告
- **文件**: App.spec.ts, login.spec.ts, WorkflowEditor.spec.ts
- **症状**: `[Vue Router warn]: No match found for location with path "/workflow"`
- **次数**: 21 次警告
- **原因**: 测试中使用了未注册的路由路径

#### Issue #2: 控制台错误输出污染  
- **文件**: login.spec.ts, SkillsView.spec.ts, SkillEditor.spec.ts
- **症状**: stderr 中有 "Failed to fetch user profile" 等错误消息
- **次数**: 7 处
- **原因**: 测试触发了错误处理路径，但未抑制 console.error

### P1 Issue 识别方法论

当所有测试都通过时，P1 技术债务隐藏在 stderr 和警告中：

```bash
# 提取测试中的警告和错误
npm test 2>&1 | grep -E "(stderr|warn|Error|FAIL)"
```

### Issue 模板标准化

```markdown
## Issue: [问题名称]

**原因**: [根本原因]
**影响**: [影响范围]
**复现命令**: `[命令]`
**Owner**: [负责人]
**清零日期**: [D+7]
**状态**: Open / Assigned / Closed
```

### 关键洞察

1. **测试通过 ≠ 没有问题**: stderr 中的警告是技术债务的早期信号
2. **P1 定义**: 不影响功能但影响开发者体验的问题
3. **Issue 化价值**: 书面追踪确保问题不会被遗忘
4. **当前状态**: 
   - P0: 全绿 ✅
   - P1: 2 个 issue 待修复 📋
   - P2: 7 个 Pydantic 弃用警告（后端）

### 产出物

- `.sisyphus/evidence/week1-p1-issues.md` - P1 issue 清单

