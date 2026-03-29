# CLAUDE.md

## ⚠️ 会话启动协议

**在回复用户的第一个消息之前，必须执行以下步骤：**

1. 读取 `requirements/INDEX.md` 确认当前活跃 REQ
2. 读取 `.claude/progress.txt` 恢复上下文
3. 在回复开头声明当前状态

**状态声明格式：**
```
📊 当前状态: [REQ编号] / [阶段] / [下一步]
```

**如果用户没有指定任务，不要主动开始实现。先确认：**
- 当前是否有活跃 REQ？
- 用户想要做什么？

---

## 🚨 实施前检查点

**在写代码之前，必须通过以下检查：**

### 检查 1: 是否需要 REQ？

| 情况 | 需要 REQ |
|------|----------|
| 涉及 3+ 文件的改动 | ✅ 是 |
| 新功能开发 | ✅ 是 |
| 架构/流程变更 | ✅ 是 |
| 单文件小改动（typo、小 bug） | ❌ 否 |
| 用户明确说"不用 REQ" | ❌ 否 |

### 检查 2: REQ 是否存在？

```
如果需要 REQ:
  ├── 有活跃 REQ → 继续实施
  └── 无活跃 REQ → 先创建 REQ，再实施
```

### 检查 3: 计划来源是什么？

**重要：** 用户给出的"实施计划"不等于 REQ！

- 用户给计划 → 询问是否需要创建 REQ → 创建 REQ → 实施
- 用户说"直接做"且符合小改动标准 → 可以跳过 REQ

### 违规示例（禁止）

```
❌ 用户提供详细计划 → 直接实施 → 结束
✅ 用户提供详细计划 → 创建 REQ → 实施 → 生成报告
```

---

## Harness Lab 治理入口

本仓库采用 Harness Lab 作为研发治理层。

### 工作方式

- **理解任务**：从 REQ 和设计稿理解范围，只加载必要的 context
- **实现任务**：遵循 `plan -> build -> verify -> fix -> record` 闭环
- **验证任务**：review / QA / ship 的结论必须落到 `requirements/reports/`
- **完成任务**：更新 REQ 状态和 `.claude/progress.txt`

### 治理命令

```bash
npm run docs:impact      # 文档影响分析
npm run docs:verify      # 文档一致性验证
npm run check:governance # 治理状态检查
npm run req:create       # 创建新 REQ
npm run req:start        # 开始 REQ
npm run req:complete     # 完成 REQ
npm run verify           # 运行质量门
```

---

## 项目约束

### 行为约束

1. **修 bug 优先于一切。** 用户报了 bug，在 bug 确认修复前不做任何其他事。
2. **改代码前先读代码。** 不要基于猜测修改文件。
3. **每次改动都要验证。** 后端改动后运行 `cd backend && uv run pytest`；前端改动后运行 `cd frontend && npm run build`。
4. **单任务原则。** 每轮只做一件事，做完确认后再接下一件。
5. **大改动先列清单。** 涉及 3 个以上文件的改动，先列出计划。

### 代码质量

6. **TypeScript 文件改完必须通过类型检查。** 使用 `npm run build`。
7. **Python 文件改完必须通过语法检查。** 使用 `python -m py_compile <file>`。
8. **不要做没被要求的事。** 不要主动添加注释、文档、重构、优化。

### 禁止事项

9. **不要在修 bug 时写文档或优化计划。**
10. **不要一次改太多文件。** 每次改动控制在 1-3 个文件内。
11. **不要吞掉错误。** 遇到测试失败或编译错误时报告给用户。

---

## Development Commands

### Frontend (`frontend/`)

```bash
npm run dev              # Dev server (port 5173)
npm run build            # Type check + production build
npm run test             # Run tests
npm run lint             # ESLint + OXLint
```

### Backend (`backend/`)

```bash
uv run uvicorn main:app --reload  # Dev server (port 8000)
uv run pytest                      # Run tests
```

---

## Project Overview

**Agent Flow Lite** — Full-stack AI agent orchestration platform.

**Tech Stack:**
- **Backend**: FastAPI + Python 3.11+ + LlamaIndex + ChromaDB
- **Frontend**: Vue 3 + Vite + TypeScript + Vue Flow + Pinia
- **AI**: DeepSeek API (LLM) + SiliconFlow API (embeddings)
