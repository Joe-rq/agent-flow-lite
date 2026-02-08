# Evidence 目录结构

**整理时间**: 2026-02-08
**说明**: 本目录存放工作执行过程中生成的证据、报告和验证数据

---

## 📁 目录结构

```
.sisyphus/evidence/
├── README.md                          # 本文件
├── latest -> post-gate-stability-quick-pass/  # 最新任务报告的符号链接
├── post-gate-stability-quick-pass/    # 当前任务的所有报告
│   ├── CI-VERIFICATION-SUCCESS.md
│   ├── ORCHESTRATION-FINAL-REPORT.md
│   ├── ORCHESTRATION-COMPLETION-STATUS.md
│   ├── blocked-final-report.md
│   ├── ci-status-tracking.md
│   ├── ci-verification-guide.md
│   ├── execution-complete-summary.md
│   ├── final-status-report.md
│   ├── post-gate-stability-quick-pass-status-20260208.md
│   ├── post-gate-stability-quick-pass-verification-20260208.md
│   └── TASK-TRANSFER-EXPLANATION.md
└── archives/                          # 历史数据存档
    ├── day0/                          # Day 0 基线数据
    ├── quality-gate/                  # 历史 Quality Gate 报告
    ├── tasks/                         # 历史任务数据
    └── week1/                         # Week 1 数据
```

---

## 📂 目录说明

### `post-gate-stability-quick-pass/`

当前完成的任务的所有相关报告和文档。

**核心文件**:
- `CI-VERIFICATION-SUCCESS.md` - CI 验证成功报告
- `ORCHESTRATION-FINAL-REPORT.md` - 最终执行报告
- `post-gate-stability-quick-pass-verification-20260208.md` - 详细验证报告

### `archives/`

历史数据和旧报告存档。

**子目录**:
- `day0/` - Day 0 基线测试数据
- `quality-gate/` - 历史 Quality Gate 相关报告
- `tasks/` - 历史任务执行数据（task-1, task-2 等）
- `week1/` - Week 1 的质量基线数据

---

## 📝 使用说明

### 查找最新报告

```bash
# 查看最新任务的报告
cd .sisyphus/evidence/latest

# 或
cd .sisyphus/evidence/post-gate-stability-quick-pass
```

### 查找历史数据

```bash
# 查看 Day 0 基线
cd .sisyphus/evidence/archives/day0

# 查看 Week 1 数据
cd .sisyphus/evidence/archives/week1

# 查看历史任务
cd .sisyphus/evidence/archives/tasks
```

### 查找特定类型的报告

```bash
# Quality Gate 相关
cd .sisyphus/evidence/archives/quality-gate
```

---

## 🔍 快速参考

| 需要查找 | 位置 |
|---------|------|
| 最新任务报告 | `latest/` 或 `post-gate-stability-quick-pass/` |
| CI 验证结果 | `post-gate-stability-quick-pass/CI-VERIFICATION-SUCCESS.md` |
| 历史基线数据 | `archives/day0/` |
| 历史任务数据 | `archives/tasks/` |
| Week 1 数据 | `archives/week1/` |

---

## 📅 整理历史

- **2026-02-08**: 首次整理，按时间和任务类型分类存档
