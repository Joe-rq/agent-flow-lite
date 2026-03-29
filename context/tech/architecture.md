# Architecture

## 总体结构

本项目保持业务运行时结构不变，只在外层引入 Harness Lab 治理协议。

```text
agent-flow-lite/
├── frontend/               # Vue 3 + Vite + TypeScript
├── backend/                # FastAPI + Pydantic + RAG / workflow APIs
├── docs/                   # 设计、测试与治理文档
├── scripts/                # 质量门与治理脚本
├── context/                # 业务 / 技术 / 经验上下文
├── requirements/           # REQ 生命周期与报告
└── .claude/progress.txt    # 跨会话进度交接
```

## 运行时边界

- `frontend/` 负责页面、工作流编辑器、对话终端和 Pinia / Router 状态
- `backend/` 负责 API、RAG、Skill 执行、工作流引擎和运行时数据
- `backend/data/` 属于运行时状态，不作为稳定源码依赖
- `docs/design/` 与 `docs/testing/` 保留项目已有设计与测试文档
- `docs/plans/` 用于与 REQ 绑定的实施方案

## 治理层边界

- Harness Lab 固定的是 REQ 流程、交付物和上下文入口顺序
- Harness Lab 不替换前后端架构，也不改写现有运行命令
- 代码变更仍需遵守本项目现有的前后端约束和测试策略