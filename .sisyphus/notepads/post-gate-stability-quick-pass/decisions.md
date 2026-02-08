# Decisions

## Task 1: E2E Frontend Server Startup

**2026-02-08T15:45:00Z**
- **选择**: 使用 `vite preview` 而非 `npm run dev`
  - **理由**: CI 环境不需要 HMR，静态服务启动更快、资源占用更低
- **选择**: 使用 `curl --retry` 而非安装新依赖
  - **理由**: 复用后端启动已有的模式，不引入新依赖
- **选择**: 在 E2E job 中重新构建前端
  - **理由**: GitHub Actions 各 job 独立 runner，构建产物不共享

---

## Task 2: Full Tests State Pollution

**2026-02-08T15:46:00Z**
- **选择**: 添加 `--isolate` 命令行标志
  - **理由**: 在命令行层面覆盖 `vit`est.config.ts` 的 `isolate: false`，强制每个测试文件独立进程
- **选择**: 不修改 `vitest.config.ts` 全局配置
  - **理由**: 避免影响本地开发体验（本地可能需要 `isolate: false` 节省资源）
- **选择**: 不逐个修复 34 个测试的隔离问题
  - **理由**: 根因在运行环境配置，不在测试代码

---

## Task 3: CI Verification

**2026-02-08T15:47:00Z**
- **等待**: GitHub Actions 工作流执行完成（约 5-10 分钟）
- **验证**: 所有 job 状态为 `success`
- **监控**: https://github.com/Joe-rq/agent-flow-lite/actions/workflows/quality-gate.yml
