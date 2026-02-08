# Quality Gate 验证指南

## 📋 快速检查清单

### 1. 访问 GitHub Actions
🔗 **直接链接**: https://github.com/Joe-rq/agent-flow-lite/actions/workflows/quality-gate.yml

### 2. 查找最近的运行
查找以下提交触发的运行：
- ✅ **Commit 2b096a2**: "test(frontend): stabilize App P0 chrome/logout assertions"
- ✅ **Commit 1f4780b**: "fix(ci): bootstrap backend uv install in quality gate"

### 3. 验证关键检查（Critical Layer）

必须全部显示 ✅ 绿色勾：

#### 前端关键检查
- [ ] **frontend-type-check** - TypeScript 类型检查
- [ ] **frontend-build** - 前端构建
- [ ] **frontend-critical-tests** - 前端 P0 测试（52个测试）

#### 后端关键检查
- [ ] **backend-critical-tests** - 后端 P0 测试（45个测试）

### 4. 验证汇总输出

点击 **Quality Gate Summary** 作业，检查输出：

**期望看到**：
```
=== QUALITY GATE DECISION ===
PASS - All critical checks passed
```

**如果看到 FAIL**，检查哪个关键检查失败了。

---

## 🔍 详细验证步骤

### Step 1: 检查工作流触发
1. 打开 https://github.com/Joe-rq/agent-flow-lite/actions
2. 确认有 "Quality Gate" 工作流运行
3. 确认触发时间在 2026-02-08 11:49 之后（commit 2b096a2 的时间）

### Step 2: 检查关键作业状态
点击最近的运行，展开作业列表：

#### ✅ 前端类型检查 (frontend-type-check)
- 应该显示绿色 ✓
- 运行时间：~30-60秒
- 关键步骤：`Run TypeScript check`

#### ✅ 前端构建 (frontend-build)
- 应该显示绿色 ✓
- 运行时间：~1-2分钟
- 关键步骤：`Build frontend`

#### ✅ 前端关键测试 (frontend-critical-tests)
- 应该显示绿色 ✓
- 运行时间：~1-2分钟
- 关键步骤：`Run P0 critical tests`
- **验证命令**：
  ```bash
  npm run test -- --run --isolate \
    src/__tests__/App.spec.ts \
    src/__tests__/views/ChatTerminal.spec.ts \
    src/__tests__/auth/login.spec.ts
  ```
- **期望输出**：`52 passed`

#### ✅ 后端关键测试 (backend-critical-tests)
- 应该显示绿色 ✓
- 运行时间：~1-2分钟
- 关键步骤：
  1. `Install backend dependencies` - 应该使用 `uv sync --group dev`
  2. `Run P0 critical tests`
- **验证命令**：
  ```bash
  uv run pytest -q \
    tests/test_auth.py \
    tests/test_chat_citation.py \
    tests/test_chat_scoped.py \
    tests/test_workflow_api.py \
    tests/test_knowledge_dimension_mismatch.py
  ```
- **期望输出**：`45 passed`

### Step 3: 检查汇总作业
点击 **quality-gate-summary** 作业：

1. 展开 `Critical checks status` 步骤
2. 确认输出包含：
   ```
   === CRITICAL LAYER (Required) ===
   frontend-type-check: success
   frontend-build: success
   frontend-critical-tests: success
   backend-critical-tests: success

   === QUALITY GATE DECISION ===
   PASS - All critical checks passed
   ```

---

## 🐛 故障排查

### 如果 backend-critical-tests 失败

**检查点 1**: 依赖安装步骤
- 查看 `Install backend dependencies` 日志
- 确认使用的是 `uv sync --group dev`（不是 `uv pip install -e ".[dev]"`）
- 确认没有 "No virtual environment found" 错误

**检查点 2**: 测试执行步骤
- 查看 `Run P0 critical tests` 日志
- 确认所有5个测试文件都被执行
- 检查是否有导入错误或运行时错误

### 如果 frontend-critical-tests 失败

**检查点 1**: 测试命令
- 确认使用了 `--isolate` 标志
- 命令应该是：`npm run test -- --run --isolate src/__tests__/...`

**检查点 2**: App.spec.ts 测试
- 如果 "should render header when user is authenticated" 失败
  - 检查是否有 `flushPromises()` 调用
- 如果 "should redirect to /login immediately after clicking logout" 失败
  - 检查是否使用了 `data-testid="logout-button"`
  - 检查是否有 `flushPromises()` 在 router.isReady() 之前

---

## 📊 本地验证（已完成）

### ✅ 后端 P0 测试
```bash
cd backend
uv sync --group dev
uv run pytest -q tests/test_auth.py tests/test_chat_citation.py tests/test_chat_scoped.py tests/test_workflow_api.py tests/test_knowledge_dimension_mismatch.py
```
**结果**: ✅ 45 passed

### ✅ 前端 P0 测试
```bash
cd frontend
npm run test -- --run --isolate src/__tests__/App.spec.ts src/__tests__/views/ChatTerminal.spec.ts src/__tests__/auth/login.spec.ts
```
**结果**: ✅ 52 passed

---

## 📝 记录结果

完成验证后，请更新此文件并记录：

### CI 运行结果
- **Run ID**: _____________
- **Run URL**: https://github.com/Joe-rq/agent-flow-lite/actions/runs/_____________
- **触发提交**: 2b096a2
- **运行时间**: _____________

### 关键检查结果
- [ ] frontend-type-check: ✅ / ❌
- [ ] frontend-build: ✅ / ❌
- [ ] frontend-critical-tests: ✅ / ❌
- [ ] backend-critical-tests: ✅ / ❌

### 汇总结果
- [ ] Quality Gate Summary: PASS / FAIL

### 截图（可选）
可以截图保存到 `.sisyphus/evidence/screenshots/` 目录。

---

## ✅ 完成标准

当以下所有条件满足时，Task 5 完成：

1. ✅ 所有4个关键检查显示 success
2. ✅ Quality Gate Summary 输出 "PASS - All critical checks passed"
3. ✅ 没有关键作业被跳过或取消
4. ✅ 运行结果已记录在本文件中

---

**生成时间**: 2026-02-08 13:35
**生成者**: Claude Code
**相关提交**: 1f4780b, 2b096a2
