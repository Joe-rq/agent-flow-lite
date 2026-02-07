# Remove Zep (Lean Plan)

## TL;DR

> 这是一个单会话可完成的清理任务，不做流程表演。
>
> 目标：彻底移除 Zep（代码、依赖、配置、测试、文档），保留非 Zep 业务行为。

---

## Scope

### IN
- 删除 Zep 运行时代码与调用链
- 删除 Zep 依赖与配置项
- 删除/改造 Zep 测试
- 清理文档与环境变量说明
- 执行回归验证

### OUT
- 不引入任何替代记忆系统
- 不做与 Zep 无关的重构
- 不改 chat stream 协议

---

## Guardrails (必须遵守)

- `backend/tests/test_chat_scoped.py` 只能手术式清理 Zep 相关测试，禁止整文件删除
- `backend/uv.lock` 只能通过 `uv lock` 重建，禁止手改
- 不得“顺手优化” `backend/app/api/chat.py` 与 Zep 无关逻辑
- 不新增功能，只做移除与修复

---

## 7-Step 执行清单

- [x] 1. 删除 `backend/app/core/zep.py`

- [x] 2. 先全量定位，再清理 `backend/app/api/chat.py` 的 Zep 调用链
  - 先跑定位命令（必须先做）：
    - `grep -R "from app.core.zep\|zep_client\|get_zep_session_id\|zep_session_id\|if zep.enabled\|memory_context" backend/app/api/chat.py`
  - 删除 `from app.core.zep import zep_client`
  - 删除 `zep_client()` 实例化与 `if zep.enabled` 分支
  - 删除 `get_zep_session_id()`
  - 去掉 `build_system_prompt(..., memory_context)` 的 Zep memory 注入

- [x] 3. 清理配置 `backend/app/core/config.py`
   - 删除 `zep_api_key` / `zep_api_url` / `zep_enabled`

- [x] 4. 清理依赖
  - `backend/pyproject.toml` 删除 `zep-cloud`
  - 执行 `cd backend && uv lock`

- [x] 5. 先读测试结构，再清理测试
  - 先检查 fixture/共享层是否有 Zep 渗透（必须先做）：
    - `grep -R "zep\|Zep\|zep_client\|get_zep_session_id\|zep_session_id" backend/tests`
    - `grep -R "zep\|Zep\|zep_client" backend/tests/conftest.py backend/tests 2>/dev/null`
  - 删除 `backend/tests/test_zep_client.py`
  - 删除 `backend/tests/test_chat_zep.py`
  - 修改 `backend/tests/test_chat_scoped.py`：仅删 Zep 相关断言/Mock，保留 ownership/session 边界测试

- [x] 6. 清理环境与文档
  - `.env.example` / README / AGENTS / CLAUDE / docs 中的 Zep 配置与说明
  - 历史复盘文档可保留“历史 bug”描述，但不得再作为当前配置指引

- [x] 7. 最终验证
  - `grep -R "from app.core.zep\|zep_client\|get_zep_session_id\|zep_session_id\|ZEP_\|zep-cloud" backend README.md backend/README.md AGENTS.md CLAUDE.md docs`
  - `cd backend && uv run pytest -q`
  - `cd backend && uv run python -c "from app.api import chat; print('OK')"`
  - `cd backend && uv run uvicorn main:app --host 127.0.0.1 --port 8000` 启动无 Zep 相关报错

---

## Definition of Done

- [x] 后端运行路径不再出现 Zep import/调用
- [x] `pyproject.toml` 与 `uv.lock` 不再包含 `zep-cloud`
- [x] Zep 专项测试移除，非 Zep 边界测试仍在且通过
- [x] 文档/环境变量说明不再指导配置 Zep
- [x] 回归测试与启动冒烟通过
