# Agent Flow Lite 项目体检报告与修复计划

> 生成时间：2026-02-12
> 检查维度：后端代码质量、前端代码质量、安全审计、依赖配置、前后端集成（5 个 agent 并行检查）
> 测试状态：后端 168 pass / 前端 158 pass / 构建通过

---

## 第一批：安全 + 数据完整性（Critical + High 核心）

### 1. [Critical] 无密码认证 — 仅凭邮箱即可登录
- **位置**: `backend/app/api/auth.py:53-98`
- **问题**: `/api/v1/auth/login` 只需提供邮箱即可获取 token，无密码、无 OAuth、无任何身份验证
- **修复**: 至少添加密码认证（bcrypt/argon2 哈希），或接入 OAuth2/OIDC

### 2. [Critical] RAG 异常被静默吞掉
- **位置**: `backend/app/api/chat.py:162`
- **问题**: `except Exception: pass`，RAG 检索失败时无日志无通知，用户不知道 RAG 功能失效
- **修复**: 至少改为 `logger.warning("RAG retrieval failed", exc_info=True)`，并考虑向前端发送降级提示

### 3. [High] Git 历史中 Token 泄露
- **位置**: commit `8037991` / `d83efbc`
- **问题**: `.claude/settings.local.json` 曾被提交，token 已泄露
- **修复**: 确认 token 已轮换；考虑用 `git filter-repo` 或 BFG 清理历史

### 4. [High] admin_email 默认值安全隐患
- **位置**: `backend/app/core/config.py` — `admin_email` 默认 `admin@mail.com`
- **问题**: 忘记配置时任何人用该邮箱注册即获管理员权限；`.env.example` 缺少此配置项
- **修复**: 移除默认值或改为空字符串；在 `.env.example` 中添加 `ADMIN_EMAIL=`

---

## 第二批：用户体验直接受损（High 交互类）

### 5. [High] SSE 连接无 AbortController
- **位置**: `frontend/src/composables/chat/useChatSSE.ts`, `useSSEStream.ts`, `useSkillRunner.ts`
- **问题**: 无法取消进行中的流，用户切换 session 时旧流继续运行可能写入错误 session，组件卸载后内存泄漏
- **修复**: 所有 fetch 调用添加 AbortController，在组件 onUnmounted / session 切换时 abort

### 6. [High] Axios 401 拦截器不覆盖 fetch 请求
- **位置**: `frontend/src/utils/axios.ts` 只拦截 axios；SSE 用原生 fetch
- **问题**: token 过期时 SSE 请求返回 401 不会自动登出
- **修复**: 在 fetch wrapper（useSSEStream/useChatSSE）中统一处理 401 → 清除 token + 跳转登录

### 7. [High] SSE HTTP 错误丢失详情
- **位置**: `useChatSSE.ts:70-72`, `useSSEStream.ts:36-38`
- **问题**: fetch 失败时不读取响应体 detail，用户只看到 "HTTP error! status: 400"
- **修复**: `if (!response.ok)` 时先 `await response.json()` 读取 detail

### 8. [High] Skill 列表缺少 inputs 字段
- **位置**: 后端 `SkillSummary` 模型 / 前端 `SkillsView.vue:94-103`
- **问题**: `SkillSummary` 不返回 inputs 数组，前端技能列表页的输入参数标签永远不显示
- **修复**: 在 `SkillSummary` 中添加 `inputs: list[SkillInput]` 字段

### 9. [High] SSE 流式响应缺少超时控制
- **位置**: 后端 `chat_stream.py` 所有 stream generator；前端所有 SSE 连接
- **问题**: LLM API 挂起时前后端都无限等待
- **修复**: 后端添加 `asyncio.timeout()`；前端添加 setTimeout 兜底

---

## 第三批：健壮性（Medium 核心）

### 10. [High] vue/no-mutating-props x4
- **位置**: `LlmNodeConfig.vue`(3), `SkillNodeConfig.vue`(1), `SkillRunDialog.vue`(1)
- **问题**: 直接修改 props 违反 Vue 单向数据流
- **修复**: 改用 `emit('update:xxx')` 或 `v-model`

### 11. [Medium] 大量 except Exception 缺少日志（约 20+ 处）
- **位置**: `chat_stream.py`, `workflow_nodes.py`, `rag.py`, `llm.py`, `skill_executor.py`, `processor.py`
- **修复**: 所有 `except Exception` 块添加 `logger.exception()` 或至少 `logger.warning()`

### 12. [Medium] Document 状态枚举不一致
- **位置**: 后端 `DocumentStatus.FAILED = "failed"` / 前端 `types/index.ts:42` 用 `"error"`
- **修复**: 统一为 `"failed"` 或 `"error"`，前后端保持一致

### 13. [Medium] 后端错误作为 token 事件污染 session 历史
- **位置**: `backend/app/api/chat_stream.py:239`
- **问题**: LLM 异常时错误信息作为 `token` 事件发送，拼接到 assistant 消息中保存到 session
- **修复**: 改为发送 `error` 事件类型，前端单独处理

### 14. [Medium] 知识库端点缺少 kb_id 格式验证
- **位置**: `backend/app/api/knowledge.py:52-79`
- **问题**: upload/list/search/get_info 端点未调用 `validate_kb_id()`，只有 delete 调用了
- **修复**: 在所有接收 kb_id 的端点统一调用 `validate_kb_id()`

### 15. [Medium] 无速率限制
- **位置**: 全局
- **问题**: 登录端点和 LLM 调用端点无速率限制
- **修复**: 引入 `slowapi` 或自定义中间件，至少限制 `/auth/login` 和 `/chat/completions`

### 16. [Medium] Workflow/Skill 执行无资源限制
- **位置**: `workflow_engine.py`, `llm.py`
- **问题**: 无超时、无最大节点数、无并发限制
- **修复**: 添加 workflow 执行超时（如 5 分钟）、最大节点数限制、用户级并发限制

### 17. [Medium] SkillInput 前端缺少 label/type 字段
- **位置**: `frontend/src/types/index.ts` SkillInput 接口
- **修复**: 添加 `label?: string` 和 `type?: string` 字段

### 18. [Medium] Pydantic V2 deprecation warnings（8 处）
- **位置**: `config.py:55`, `admin.py:23`, `auth.py:38`, `workflow.py:40`, `document.py:42,56,73`
- **修复**: `class Config` → `model_config = ConfigDict(...)`

### 19. [Medium] CORS allow_methods/headers 过于宽松
- **位置**: `backend/main.py:68-75`
- **修复**: `allow_methods=["GET","POST","PUT","DELETE","OPTIONS"]`, `allow_headers=["Authorization","Content-Type"]`

### 20. [Medium] Workflow 直接执行 vs Chat 执行 SSE 协议不统一
- **位置**: `workflow.py:198-223` vs `chat_stream.py:297-380`
- **问题**: 同一 workflow 两条路径的 SSE 事件类型完全不同
- **修复**: 统一为标准协议，或在 workflow API 中也做事件转换

---

## 第四批：代码质量 + 配置（Medium 次要 + Low）

### 21. [Medium] no-explicit-any x9
- **位置**: `NodeConfigPanel.vue`, `useSkillForm.ts`, `useUserAdmin.ts`, `useNodeConfig.ts`, `useWorkflowCrud.ts`
- **修复**: 逐个替换为具体类型

### 22. [Medium] 后端依赖全部 `>=` 无上限约束
- **位置**: `backend/pyproject.toml`
- **修复**: 关键依赖加上限（如 `fastapi>=0.128.0,<1.0`）

### 23. [Medium] processing_tasks 内存字典多 worker 不一致
- **位置**: `backend/app/core/knowledge/store.py:18,136`
- **修复**: 当前单进程无问题，扩展时需改为 Redis 或数据库存储

### 24. [Medium] CI type-check 重复执行
- **位置**: `.github/workflows/quality-gate.yml`
- **修复**: frontend-build 去掉对 frontend-type-check 的依赖，或 build 只运行 `build-only`

### 25. [Low] SkillLoader 重复实例化
- **位置**: `skill.py:35`, `chat_stream.py:32`, `workflow_nodes.py:50`
- **修复**: 统一使用单例或工厂函数

### 26. [Low] DATA_DIR 路径计算重复
- **位置**: `workflow.py:29`, `database.py:12`（未使用已有的 `paths.py`）
- **修复**: 统一使用 `app/core/paths.py` 中的 `BACKEND_DATA_DIR`

### 27. [Low] 根目录散落文件清理
- 空文件 `EOF`、根目录 `node_modules/` + `package-lock.json`、`backend/test_chat_api.py` + `test_deepseek.py`
- **修复**: 删除 EOF，清理根目录 node_modules，移动测试文件到 tests/

### 28. [Low] ChatTerminal.vue eslint 假阳性
- **位置**: 4 个 "unused vars" 实际被测试通过 `setupState` 访问
- **修复**: 添加 `// eslint-disable-next-line @typescript-eslint/no-unused-vars`

### 29. [Low] HomeView.vue 超 200 行 + CSS 提取不一致
- **位置**: `HomeView.vue`(226行), `LoginView.vue` + 10 个 component 使用内联 style
- **修复**: 提取 CSS 到 co-located .css 文件

### 30. [Low] @skill 解析位置前后端不一致
- **位置**: 后端 `chat.py:50` 只匹配开头 / 前端 `useSkillAutocomplete.ts:32` 允许中间
- **修复**: 统一行为，前端自动补全也限制在消息开头

---

## 确认无问题的项目（Info）

- SQL 注入防护：全 ORM，无原始 SQL 拼接 ✅
- XSS 防护：前端无 v-html 使用 ✅
- 文件上传防护：类型限制 + 大小限制 + 路径遍历检查 ✅
- FileLock 使用：模式正确 ✅
- Vitest 资源约束：pool/maxForks/maxConcurrency 配置完善 ✅
- uv.lock 与 pyproject.toml 同步 ✅
- CI Quality Gate 分层设计合理 ✅
- 前端依赖无未声明/未使用问题 ✅
- Composables 按域组织结构清晰 ✅
