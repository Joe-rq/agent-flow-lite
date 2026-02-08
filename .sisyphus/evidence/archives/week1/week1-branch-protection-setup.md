# Week 1 分支保护与 Required Checks 配置文档

> **状态**: 待管理员手动配置（Week 1 不自动启用）
> **创建日期**: 2026-02-07
> **文档版本**: 1.0

## 概述

本文档记录了 `agent-flow-lite` 仓库的分支保护规则与 Required Checks 配置。配置定义了 4 个必须通过的 CI 检查，这些检查通过后才能将 Pull Request 合并到 `main` 分支。

## Required Checks 列表

以下 4 个检查来自 `.github/workflows/quality-gate.yml`，是合并前的**强制通过项**：

| 检查名称 | 描述 | 所属层 |
|---------|------|-------|
| `frontend-type-check` | TypeScript 类型检查 | Critical Layer |
| `frontend-build` | 前端生产构建 | Critical Layer |
| `frontend-critical-tests` | 前端 P0 关键测试（3个测试文件） | Critical Layer |
| `backend-critical-tests` | 后端 P0 关键测试（5个测试文件） | Critical Layer |

### 检查详细说明

**frontend-type-check**
- 运行命令: `npm run type-check`
- 验证 TypeScript 类型正确性

**frontend-build**
- 运行命令: `npm run build-only`
- 前端生产构建验证
- 依赖: `frontend-type-check` 必须先通过

**frontend-critical-tests**
- 测试文件:
  - `src/__tests__/App.spec.ts`
  - `src/__tests__/views/ChatTerminal.spec.ts`
  - `src/__tests__/auth/login.spec.ts`
- 依赖: `frontend-build` 必须先通过

**backend-critical-tests**
- 测试文件:
  - `tests/test_auth.py`
  - `tests/test_chat_citation.py`
  - `tests/test_chat_scoped.py`
  - `tests/test_workflow_api.py`
  - `tests/test_knowledge_dimension_mismatch.py`

## 分支保护配置步骤

### 方式一：使用 GitHub CLI（推荐）

```bash
gh api repos/:owner/:repo/branches/main/protection \
  -X PUT \
  -F enforce_admins=true \
  -F required_status_checks='{
    "strict": true,
    "contexts": [
      "frontend-type-check",
      "frontend-build",
      "frontend-critical-tests",
      "backend-critical-tests"
    ]
  }' \
  -F required_pull_request_reviews='{"required_approving_review_count": 1}'
```

**参数说明**：
- `enforce_admins=true`: 管理员也必须通过检查
- `strict=true`: 分支必须同步最新 base 才可合并
- `contexts`: 4 个 required checks
- `required_approving_review_count=1`: 至少 1 个批准

### 方式二：使用 GitHub Web UI

1. 进入仓库设置: `https://github.com/:owner/:repo/settings/branches`
2. 点击 "Add branch protection rule"
3. 填写规则名称（如 `main`）
4. 勾选以下选项:
   - [x] Require pull request reviews before merging
     - 设置: Required approving reviews: 1
   - [x] Require status checks to pass before merging
     - 点击 "Select checks"，选择:
       - `frontend-type-check`
       - `frontend-build`
       - `frontend-critical-tests`
       - `backend-critical-tests`
   - [x] Require branches to be up to date before merging
   - [x] Do not allow bypassing the above settings

### 方式三：使用 Terraform（如仓库使用 IaC）

```hcl
resource "github_branch_protection" "main" {
  repository              = "agent-flow-lite"
  branch                  = "main"
  enforce_admins           = true

  required_pull_request_reviews {
    required_approving_review_count = 1
  }

  required_status_checks {
    strict = true
    contexts = [
      "frontend-type-check",
      "frontend-build",
      "frontend-critical-tests",
      "backend-critical-tests"
    ]
  }

  # 防止任何人绕过保护规则
  lock_branch = false
  allow_force_push {
    actor = []
  }
}
```

## 紧急回滚预案

### 场景：需要绕过检查快速修复生产问题

**仅限以下情况使用紧急例外**：
- 生产环境严重故障（如服务完全不可用）
- 安全漏洞修复
- 紧急热修复（hotfix）

### 紧急例外申请流程

1. **申请**: 在 Slack/Teams 或应急通讯渠道发布紧急例外请求
2. **审批**: 至少 1 名维护者审批
3. **记录**: 使用以下模板创建 Issue:

```markdown
---
title: "[紧急例外] 绕过分支保护
labels: emergency-bypass, production-hotfix
---

## 紧急例外申请

**申请人**: @username
**审批人**: @approver
**时间**: YYYY-MM-DD HH:MM

### 紧急情况描述
<!-- 描述生产问题的严重性 -->

### 受影响范围
<!-- 影响的服务/用户 -->

### 变更内容
<!-- 将要提交的代码变更概述 -->

### 绕过检查
- [ ] frontend-type-check
- [ ] frontend-build
- [ ] frontend-critical-tests
- [ ] backend-critical-tests

### 后续行动项
- [ ] 在紧急修复后 24 小时内补交测试
- [ ] 创建 Tech Debt Issue 记录遗漏的测试
```

### 绕过检查的操作方式

```bash
# 1. 使用管理token强制推送（谨慎使用）
git push origin <branch> --force-with-lease

# 2. 在 GitHub PR 中添加 "bypass" 标签
# 需要在仓库设置中预先配置 bypass 规则

# 3. 临时修改分支保护规则（需管理员权限）
# 使用后立即恢复
```

### 回滚执行步骤

1. **立即记录**: 创建 Issue 记录紧急例外详情
2. **临时修复**: 执行必要的代码变更
3. **补充测试**: 在 24 小时内补充遗漏的测试
4. **清理**: 关闭紧急例外 Issue
5. **复盘**: 在周会中复盘紧急例外情况

## 配置验证

配置完成后，验证以下场景：

### 场景 1：PR 未通过检查

- 创建测试 PR，包含失败的测试
- 验证: "This branch cannot be merged" 提示出现
- 验证: 合并按钮被禁用

### 场景 2：PR 缺少批准

- 创建 PR，不请求审查
- 验证: 合并按钮提示 "Reviews required"

### 场景 3：PR 未同步最新 base

- 创建 PR，base 分支有更新
- 验证: "This branch is out-of-date with the base branch" 提示出现

## 相关文档

- CI 配置: `.github/workflows/quality-gate.yml`
- Week 1 计划: `.sisyphus/plans/week1-quality-baseline.md`
- 决策记录: `.sisyphus/notepads/week1-quality-baseline/decisions.md`

## 更新日志

| 版本 | 日期 | 变更内容 |
|-----|------|---------|
| 1.0 | 2026-02-07 | 初始版本，记录 4 个 required checks |
