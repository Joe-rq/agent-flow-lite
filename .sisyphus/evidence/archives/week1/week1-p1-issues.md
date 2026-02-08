# Week 1 P1 非阻断失败 Issue 清单

**生成时间**: 2026-02-07  
**测试范围**: 前端 164 测试 + 后端 159 测试  
**P0 状态**: ✅ 全绿（Task 3 已修复）  
**总 P1 Issues**: 2

---

## 执行摘要

全量测试通过后，识别出 2 个 P1 级别技术债务问题：
1. Vue Router 路径未匹配警告（测试污染）
2. 控制台错误输出污染（stderr 噪音）

这些问题**不阻断 CI/CD**，但影响：
- 测试输出的可读性
- 开发者的调试体验
- 潜在的测试可靠性隐患

---

## Issue #1: Vue Router 路径未匹配警告

**原因**: 测试中使用了未在 mock router 中注册的路由路径
**影响**: 测试输出被 Vue Router warn 污染，降低可读性
**复现命令**: `cd frontend && npm test -- src/__tests__/App.spec.ts`
**Owner**: @frontend-team
**清零日期**: 2026-02-14
**状态**: Open

### 受影响文件
| 文件 | 警告次数 | 具体路径 |
|------|----------|----------|
| `App.spec.ts` | 12 | /workflow, /knowledge, /chat, /skills |
| `login.spec.ts` | 8 | /workflow, /knowledge, /chat, /skills |
| `WorkflowEditor.spec.ts` | 1 | / |

### 错误样例
```
[Vue Router warn]: No match found for location with path "/workflow"
[Vue Router warn]: No match found for location with path "/knowledge"
[Vue Router warn]: No match found for location with path "/chat"
[Vue Router warn]: No match found for location with path "/skills"
```

### 修复建议
1. 在测试 setup 中注册完整路由表
2. 或使用 `createRouter({ routes: [...] })` 替代 stub
3. 或添加全局 route stub 配置

---

## Issue #2: 控制台错误输出污染

**原因**: 测试触发了错误处理路径，但未抑制 console.error 输出
**影响**: stderr 被错误日志污染，掩盖真正的测试问题
**复现命令**: `cd frontend && npm test 2>&1 | grep "stderr"`
**Owner**: @qa-team
**清零日期**: 2026-02-14
**状态**: Open

### 受影响文件及场景
| 文件 | 场景 | 错误消息 |
|------|------|----------|
| `login.spec.ts` | Auth Store /me 失败 | Failed to fetch user profile: Error: Network Error |
| `login.spec.ts` | Refresh-Logout Bug | Failed to fetch user profile: Error: Network Error |
| `SkillsView.spec.ts` | API 错误处理 | 加载技能列表失败: Error: Network error |
| `SkillsView.spec.ts` | 删除失败 | 删除技能失败 |
| `SkillsView.spec.ts` | SSE Run 失败 | 运行技能失败: Error: Network error |
| `SkillEditor.spec.ts` | 保存失败 | 保存技能失败 |
| `SkillEditor.spec.ts` | 加载失败 | 加载技能失败: Error: Not found |

### 错误样例
```
stderr | src/__tests__/views/SkillsView.spec.ts > SkillsView Skill List > should handle API error when loading skills
加载技能列表失败: Error: Network error
```

### 修复建议
1. 在测试中 mock `console.error` 或 `console.warn`
2. 使用 `vi.spyOn(console, 'error').mockImplementation(() => {})`
3. 或使用 `expect(console.error).toHaveBeenCalledWith(...)` 显式断言错误输出

---

## Issue 优先级矩阵

| Issue | 严重性 | 频率 | 修复成本 | 优先级 |
|-------|--------|------|----------|--------|
| #1 Vue Router 警告 | 低 | 高（21次） | 低 | P1-High |
| #2 控制台错误污染 | 低 | 中（7处） | 低 | P1-Medium |

---

## 本地 Issue 编号映射

| 本地编号 | 问题描述 | 目标 GitHub Issue |
|----------|----------|-------------------|
| P1-001 | Vue Router 路径未匹配警告 | [待创建] |
| P1-002 | 控制台错误输出污染 | [待创建] |

---

## 验证清单

- [x] 运行全量测试识别所有非阻断问题
- [x] 分类整理 P1 级别技术债务
- [x] 为每个问题分配 Owner 和 Deadline
- [x] 提供复现命令和修复建议
- [ ] 创建 GitHub Issue 并更新 URL（需人工执行）

---

## 附录：测试统计

### 前端测试 (vitest)
```
Test Files  12 passed (12)
Tests       164 passed (164)
Duration    2.08s
```

### 后端测试 (pytest)
```
Test Files  11 passed
Tests       159 passed
Warnings    7 (Pydantic deprecation warnings - P2 级别)
```

---

*Ultraworked with [Sisyphus](https://github.com/code-yeongyu/oh-my-opencode)*
