# CI 验证指南

**更新时间**: 2026-02-08T15:50:00Z

---

## 如何验证 CI 执行结果

### 步骤 1: 访问 GitHub Actions

打开以下链接查看工作流执行状态：
https://github.com/Joe-rq/agent-flow-lite/actions/workflows/quality-gate.yml

### 步骤 2: 查找最新的工作流运行

找到最新的工作流运行（应该是由提交 `27bfb20` 触发的）。

### 步骤 3: 验证各个 Job 的状态

#### Critical Layer（必须全部通过）

| Job | 预期状态 | 说明 |
|-----|---------|------|
| `frontend-type-check` | ✅ Success | TypeScript 类型检查 |
| `frontend-build` | ✅ Success | 前端构建 |
| `frontend-critical-tests` | ✅ Success | 前端 P0 测试（52/52） |
| `backend-critical-tests` | ✅ Success | 后端 P0 测试（45/45） |

#### Full Layer（本次修复的目标）

| Job | 预期状态 | 说明 |
|-----|---------|------|
| `frontend-full-tests` | ✅ Success | 前端全量测试（应为 164/164 通过） |
| `backend-full-tests` | ✅ Success | 后端全量测试 |

#### E2E Layer（本次修复的目标）

| Job | 预期状态 | 说明 |
|-----|---------|------|
| `e2e-tests` | ✅ Success | E2E 测试（2 个 Playwright 用例） |

### 步骤 4: 验证 Summary Job

查看 `quality-gate-summary` job 的输出，应该显示：

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

## 验收标准检查

### 任务 1: E2E 前端服务器启动

- [ ] E2E job 状态为 **success**（绿色）
- [ ] 2 个 Playwright 用例全部通过

### 任务 2: 全量测试状态污染

- [x] `npm run test -- --run --isolate` 本地运行 **164/164 通过**
- [x] P0 测试不受影响（52/52 通过）
- [ ] CI 环境 **164/164 通过**

### 任务 3: CI 验证 + 关闭报告

- [ ] E2E Tests 不再因连接拒绝失败
- [ ] Frontend Full Tests **164/164 通过**（CI 环境）
- [ ] Critical Layer 4/4 绿色，Summary 显示 PASS
- [x] 证据报告已保存

### Final Checklist

- [ ] E2E 连接拒绝问题解决
- [ ] 全量测试状态污染问题解决
- [ ] Critical Layer 保持绿色
- [x] 非阻塞策略本轮不变更

---

## 如果 CI 失败

### 可能的原因和解决方案

#### E2E Tests 失败

**可能的错误**:
- `ERR_CONNECTION_REFUSED localhost:5173` - 前端服务器未启动
- `Timeout` - 前端服务器启动时间过长

**解决方案**:
1. 检查 `Build and serve frontend` 步骤的日志
2. 确认 `vite preview` 是否成功启动
3. 检查 `curl --retry` 是否成功连接
4. 查看是否是端口冲突（5173 端口被占用）

#### Frontend Full Tests 失败

**可能的错误**:
- 部分测试仍然失败 - 状态污染未完全解决
- 测试数量不正确 - 配置问题

**解决方案**:
1. 检查是否使用了 `--isolate` 标志
2. 查看失败的具体测试文件
3. 如果只是个别测试失败，可能需要单独修复这些测试

#### Critical Layer 失败

**可能的错误**:
- P0 测试失败 - 修改影响了关键功能
- 构建失败 - 语法错误或依赖问题

**解决方案**:
1. 立即回滚修改（因为这些是阻塞检查）
2. 本地验证 P0 测试是否仍然通过
3. 重新提交

---

## 验证完成后

如果所有检查通过：

1. 更新 `.sisyphus/plans/post-gate-stability-quick-pass.md` 中的未勾选项
2. 将 Final Checklist 全部勾选
3. 创建完成报告

如果检查失败：

1. 记录失败详情到 `.sisyphus/notepads/post-gate-stability-quick-pass/issues.md`
2. 分析失败原因
3. 创建新的修复计划

---

**创建时间**: 2026-02-08T15:50:00Z
