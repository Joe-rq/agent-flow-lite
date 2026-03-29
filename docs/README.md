# 项目文档

本目录包含 Agent Flow Lite 项目的详细文档。

## 📁 目录结构

```
docs/
├── design/          # 设计文档
│   ├── prd.md                      # 产品需求文档
│   ├── prd-gap-analysis.md         # PRD 差距分析
│   ├── api_docs.md                 # API 接口文档
│   ├── db_schema.md                # 数据库设计
│   ├── tech_stack_analysis.md      # 技术栈分析
│   ├── implementation_plan.md      # 实现计划
│   └── skill-system-design.md      # Skill 系统技术设计
│
├── testing/         # 测试文档
│   ├── manual-test-guide.md        # 手动测试指南
│   ├── test-manual-checklist.md    # 测试检查清单
│   ├── node-config-test-report.md  # 节点配置测试报告
│   └── demo_script.md              # 演示脚本
│
├── code-review-fix-plan.md         # 代码审查修复计划
├── presentation_script.md          # 演示脚本
├── workflow-tutorials.md           # 工作流教程
├── vibe-coding-guide.html          # Vibe Coding 指南
├── README.md                       # 文档总索引（当前文件）
│
└── archive/         # 归档文档
    ├── CODE_REVIEW_REPORT.md       # 代码审查报告
    ├── OPTIMIZATION_PLAN.md        # 优化计划
    └── task.md                     # 任务列表
```

## 📖 文档说明

### 设计文档 (design/)

包含项目的设计和规划文档：

- **prd.md** - 产品需求文档，定义核心功能和用户故事
- **prd-gap-analysis.md** - PRD 差距分析，识别实现与需求的偏差
- **api_docs.md** - API 接口详细说明
- **db_schema.md** - 数据库表结构和关系设计
- **tech_stack_analysis.md** - 技术选型分析和决策依据
- **implementation_plan.md** - 功能实现计划和里程碑
- **skill-system-design.md** - Skill 系统技术设计（数据模型、API、实现方案）

### 测试文档 (testing/)

包含测试相关的文档和报告：

- **manual-test-guide.md** - 手动测试步骤和用例
- **test-manual-checklist.md** - 测试检查清单
- **node-config-test-report.md** - 工作流节点配置测试结果
- **demo_script.md** - 产品演示脚本

### 根目录文档

- **code-review-fix-plan.md** - 代码审查问题修复计划
- **presentation_script.md** - 产品演示脚本
- **workflow-tutorials.md** - 工作流使用教程

### 归档文档 (archive/)

包含历史文档和已完成的计划：

- **CODE_REVIEW_REPORT.md** - 代码审查报告
- **OPTIMIZATION_PLAN.md** - 性能优化计划
- **task.md** - 历史任务列表

## 🔗 快速链接

- [返回项目主页](../README.md)
- [开发规范](../AGENTS.md)
- [Claude Code 指南](../CLAUDE.md)

## ✅ CI 与质量门文档入口（2026-02 更新）

<!-- HARNESS-LAB:BEGIN -->
### 🧭 Governance 文档入口

Harness Lab 接入后，新增这些治理入口：

- `../requirements/INDEX.md`：当前活跃 / 已完成 REQ
- `../requirements/REQ_TEMPLATE.md`：REQ 模板
- `../docs/plans/`：与 REQ 绑定的实施方案
- `../requirements/reports/`：code review / QA / ship 报告
- `../context/`：业务 / 技术 / 经验上下文

历史设计和测试文档继续保留在当前目录结构中；后续新变更优先走 `requirements/` + `docs/plans/`。
<!-- HARNESS-LAB:END -->

最近提交新增了 CI 检查脚本和质量门流程，建议优先使用以下入口：

- `../scripts/verify-quality-gate.sh`：本地一键预检（前端类型检查/构建/关键测试 + 后端关键测试）
- `../scripts/check-ci-status.sh`：推送后查看最新 GitHub Actions 运行状态
- `../.github/workflows/quality-gate.yml`：Quality Gate 工作流定义
- `../.github/workflows/opencode.yml`：OpenCode 相关工作流定义

如需查看质量门执行记录，可参考：

- `../.sisyphus/evidence/README.md`
- `../.sisyphus/evidence/post-gate-stability-quick-pass/`
