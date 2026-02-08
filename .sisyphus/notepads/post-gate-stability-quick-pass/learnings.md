# Learnings

## Task 1: E2E Frontend Server Startup

**2026-02-08T15:45:00Z**
- 使用 `vite preview` 模式启动前端服务器，比 `npm run dev` 更适合 CI 环境
- 使用 `curl --retry` 进行就绪探测，确保服务器完全启动后再执行测试
- 保存进程 PID 到 `/tmp/` 临时文件，用于后续清理
- 清理步骤必须使用 `if: always()` 确保即使测试失败也能清理

---

## Task 2: Full Tests State Pollution

**2026-02-08T15:46:00Z**
- `vitest.config.ts` 中的 `isolate: false` 会导致测试文件间共享全局状态
- 使用 `--isolate` 命令行标志可以覆盖全局配置，强制每个测试文件独立进程
- 本地验证：`npm run test -- --run --isolate` 成功通过 164/164 测试
- 该方案已在 P0 测试中验证可行（`.github/workflows/quality-gate.yml:107`）

---

## Task 3: CI Verification

**2026-02-08T15:47:00Z**
- 本地验证全部通过：
  - 前端全量测试: 164/164 通过
  - 前端 P0 测试: 52/52 通过
  - 后端 P0 测试: 45/45 通过
- CI 工作流已触发，等待 GitHub Actions 执行完成
