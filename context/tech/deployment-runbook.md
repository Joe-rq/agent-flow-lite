# Deployment Runbook

## Local Startup

- Windows：`start.bat`
- macOS / Linux：`./start.sh`
- 手动模式：
  - `cd frontend && npm run dev`
  - `cd backend && uv run uvicorn main:app --reload`

## Pre-merge Verification

- `npm run verify`
- 如改动了治理入口或协议文件，再运行：
  - `npm run docs:impact`
  - `npm run docs:verify`
  - `npm run check:governance`

## Smoke Checklist

- 登录与鉴权正常
- Chat SSE 正常返回
- Workflow 编辑与执行正常
- Knowledge Base 上传与检索正常
- Skill 列表、执行与 `@skill` 调用正常

## Rollback

- 代码层回退优先使用 Git 回滚到上一个稳定提交
- 如果问题涉及 embedding 模型变更或数据不兼容，需要同时评估 `backend/data/chromadb/` 是否需要重建