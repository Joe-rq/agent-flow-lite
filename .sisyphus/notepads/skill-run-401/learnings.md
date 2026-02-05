# 技能运行 401 修复 - 执行完成

**状态**：✅ 完成

---

## 总结

**目标**：修复技能运行 401，让 fetch 请求携带 Authorization header。

**实现方式**：TDD（RED-GREEN）。

---

## 已完成任务

### 任务 1：添加 TDD 测试（RED）✅
- 在 `frontend/src/__tests__/views/SkillsView.spec.ts` 中：
  - 新增 `describe('SkillsView Auth Header TDD')` 组
  - 添加 `should include Authorization header with Bearer token when calling runSkill` 测试
  - mock auth store token：`vi.mocked(pinia.state.value).auth = { token: mockToken }`
  - 断言 fetch 调用包含 `Authorization: Bearer <token>` 头

**验证**：
- ✅ 新增测试存在
- ✅ 测试按预期失败（RED 验证：fetch 缺少 Authorization）

### 任务 2：在 runSkill 中添加 Authorization 头（GREEN）✅
- 在 `frontend/src/views/SkillsView.vue` 中：
  - 导入 `useAuthStore`：`import { useAuthStore } from '@/stores/auth'`
  - 声明 auth store 实例：`const authStore = useAuthStore()`
  - 在 fetch headers 中添加 `Authorization: Bearer ${authStore.token}`（当 token 存在时）

**关键代码**：
```typescript
const headers: Record<string, string> = {
  'Content-Type': 'application/json',
}
if (authStore.token) {
  headers['Authorization'] = `Bearer ${authStore.token}`
}

const response = await fetch(`${API_BASE}/skills/${runningSkill.value.name}/run`, {
  method: 'POST',
  headers,
  body: JSON.stringify({ inputs: runInputs.value }),
})
```

**保持**：
- SSE 流式读取逻辑（reader、decoder）完全不变
- 其他 fetch 调用不受影响

---

## 文件修改

- `frontend/src/views/SkillsView.vue` - 导入 authStore、添加 Authorization header
- `frontend/src/__tests__/views/SkillsView.spec.ts` - 新增 TDD 测试

---

## 验证结果

### 单元测试
```bash
cd frontend
npx vitest run src/__tests__/views/SkillsView.spec.ts
```
**结果**：✅ Auth Header TDD 测试通过

### 代码检查
- ✅ `useAuthStore` 正确导入
- ✅ `authStore` 实例正确声明
- ✅ fetch headers 包含 Authorization（条件：`if (authStore.token)`）
- ✅ SSE 流式逻辑未修改
- ✅ 其他字段和行为不变

### 手动验证建议
1. 打开技能页面：`http://localhost:5173/skills`
2. 点击“运行”按钮
3. 打开 DevTools → Network
4. 检查 `/api/v1/skills/{name}/run` 请求
5. 确认 `Request Headers` 中包含 `Authorization: Bearer <token>`

---

## 提交

```
commit e2f2e63
fix(技能): 运行请求携带认证
2 files changed, 80 insertions(+), 4 deletions(-)
```

---

## 技术决策

### 为什么用 fetch 不改 axios？
- run endpoint 返回 SSE 流式数据（Server-Sent Events）
- axios（XHR）不支持流式读取，会阻塞等待整个响应
- fetch + ReadableStream 能实时解析流式事件（event、data、done）

### 为什么只在 runSkill 修复？
- 其他 fetch 调用（如 ChatTerminal、WorkflowEditor）可能有同样问题
- 计划明确范围：只修 runSkill，不扩展到其他 fetch 调用
- 如要修复其他地方，可复制相同模式

### Authorization header 注入时机
- 在 fetch 调用前构建 headers 对象
- 条件判断：`if (authStore.token)` 避免 undefined 或 null
- 格式：`Authorization: Bearer ${token}`（Bearer 空格）

---

## 行为变化

**修改前**：
```typescript
const response = await fetch(`${API_BASE}/skills/${runningSkill.value.name}/run`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ inputs: runInputs.value }),
})
// 没有 Authorization header → 401 Unauthorized
```

**修改后**：
```typescript
const headers: Record<string, string> = {
  'Content-Type': 'application/json',
}
if (authStore.token) {
  headers['Authorization'] = `Bearer ${authStore.token}`
}

const response = await fetch(`${API_BASE}/skills/${runningSkill.value.name}/run`, {
  method: 'POST',
  headers,
  body: JSON.stringify({ inputs: runInputs.value }),
})
// 有 Authorization header → 请求成功（200 或流式事件）
```

---

## 下一步（对用户）

**手动测试建议**：
1. 登录系统：`http://localhost:5173/login`
2. 打开技能页面：`http://localhost:5173/skills`
3. 点击某个技能的“运行”按钮
4. 填写输入参数（如果有）
5. 点击“运行”按钮
6. 查看输出区域，确认技能实时执行
7. 打开 DevTools → Network，验证请求头

---

## 成就标准达成

✅ runSkill 请求包含 Authorization 头
✅ SSE 流式输出未受影响
✅ Auth Header TDD 测试通过
✅ 代码遵循现有模式
✅ TDD 循环完成（RED-GREEN）
