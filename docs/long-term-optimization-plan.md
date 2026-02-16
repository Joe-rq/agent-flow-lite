# Agent Flow Lite 长期优化方案 v3

> 基于 Dify / LangFlow / Flowise / Coze / FastGPT 竞品调研 + 代码深度分析
> v1 编写：2026-02-15 | v2 修订：2026-02-15 | v3 修订：2026-02-15
> v2 核心改动：砍掉平台化幻想，切到分发驱动，安全前移，每阶段加硬约束
> v3 核心改动：修正代码事实误判，安全闸门写死，加模板留存漏斗，代码/HTTP 节点加强隔离

---

## 一、项目定位与硬边界

**定位**：轻量级 AI Agent 编排工具 — 面向个人开发者和小团队，5 分钟部署，开箱即用。

**"轻量级"硬边界（不满足则需求一律延后）**：

| 约束 | 指标 |
|------|------|
| 部署复杂度 | 单机 `docker compose up` 完成，不超过 3 个容器 |
| 维护成本 | 1-2 人可维护全部代码 |
| 核心路径延迟 | 聊天首 token P95 < 2s（不含 LLM 推理），知识库检索 P95 < 500ms |
| 资源占用 | 空载内存 < 512MB，单机支撑 50 并发用户 |
| 新功能准入 | 不引入独立服务（沙箱、消息队列、插件守护进程等） |

**不做清单（全局）**：
- 不做插件市场 / Skill 市场（社区生态是大团队的活）
- 不做多渠道发布（微信/飞书/钉钉机器人 — 集成维护成本高，ROI 低）
- 不做 MCP Server（先证明有人用，再考虑互联）
- 不做多租户 / 工作空间 / 团队权限（面向个人和小团队，admin/user 两级够用）
- 不做子工作流嵌套（复杂度爆炸，用户也不一定需要）

---

## 二、推进策略：分发驱动，不是功能驱动

v1 的问题是"功能清单驱动"——列了一堆竞品有的功能然后排优先级。这会导致做了很多功能但没人用。

v2 切换到"分发驱动"：先做 2 个可复制的模板场景，拿到真实留存数据，再决定下一步投入。

**两个锚定场景**：

| 场景 | 用户画像 | 核心路径 | 成功标准 |
|------|---------|---------|---------|
| 知识库问答助手 | 有内部文档的小团队 | 上传 PDF → 自动索引 → 聊天问答 → 引用溯源 | 用户上传文档后 3 分钟内完成首次问答 |
| 内部 SOP 助手 | 需要标准化流程的团队 | 创建工作流 → 配置节点 → 运行 → 嵌入到内部系统 | 工作流从创建到可用 < 10 分钟 |

所有功能开发优先服务这两个场景。场景跑不通的功能不做。

### 经营方式：模板留存漏斗

不按"Phase 完成度"自我感动，改成漏斗经营：

```
激活率 → 7 日留存 → 复用率
```

- 每周只允许 1 个新能力进入主干分支，其他全部进候选池
- 每个能力上线前必须回答：它改善漏斗哪一层？预期提升多少？
- 每两周回顾一次漏斗数据，砍掉对漏斗无贡献的在建项

### 阶段闸门（硬性，不可跳过，机器强制执行）

闸门不是文本承诺，是代码说了算。规则定义在 `gates.yaml`，CI 通过 `scripts/verify_gates.py` 强制执行，检查失败直接阻断 merge。

```bash
# 检查 P1 出口闸门
uv run --project backend --group dev python scripts/verify_gates.py --phase p1_to_p2

# 检查所有闸门（当前状态快照）
uv run --project backend --group dev python scripts/verify_gates.py --all
```

| 闸门 | 条件 | 不过则 |
|------|------|--------|
| P1 → P2 | slowapi 限流生效 + 审计日志结构化字段完整 + token 计量写入日志 + pytest-cov 已安装 | P2 一律不启动 |
| P2 → P3 | 两个模板各有 ≥ 5 个真实用户完成端到端流程 + P2 功能全部有 feature flag + SSRF 防护模块存在 + 代码节点安全措施到位 | P3 不启动 |
| P3 → P4 | 测试覆盖率 ≥ 70% + Alembic 迁移已集成 | P4 不启动 |

---

## 三、阶段规划总览

| 阶段 | 周期 | 主题 | 交付物 |
|------|------|------|--------|
| Phase 1 | 第 1-2 月 | 地基：能跑通两个场景 | 上下文优化 + 多模型 + PDF 支持 + 安全闸门 |
| Phase 2 | 第 3-5 月 | 实用：场景跑顺 + 可分发 | 工作流增强 + 混合检索 + 嵌入/API 发布 |
| Phase 3 | 第 6-8 月 | 稳定：还债 + 可维护 | 存储迁移 + 代码去重 + 测试补全 |
| Phase 4 | 第 9-12 月 | 验证后决策 | 根据留存数据决定方向（见末尾决策树） |

---

## 四、Phase 1 — 地基（第 1-2 月）

> 让两个锚定场景跑通，同时把安全底线拉起来。

**北极星指标**：两个场景端到端可用，各完成 1 个真实用户验证。

**DOD（验收标准）**：
- 上下文窗口策略可配置，长对话不丢失也不超 token 限制
- 至少支持 3 个模型提供商可切换
- 知识库支持 PDF 上传和检索
- **P1 出口闸门（硬性）**：slowapi 限流生效 + 审计日志可查 + token 计量写入日志，三件套不过线 P2 一律不启动
- `uv run pytest` 全绿，`npm run build` 通过

**Kill List（本阶段不做）**：
- 不做代码执行节点、HTTP 请求节点（工作流增强是 Phase 2）
- 不做混合检索 / Rerank（先让基础检索跑通）
- 不做工作流导出/导入
- 不做前端代码重构（SSE 去重、Toast 替换等推到 Phase 3）

### 1.1 上下文策略优化

**现状**：`chat.py:172` 已有 `session.messages[-MAX_HISTORY_MESSAGES:]` 拼接最近 10 轮历史，`useChatSSE.ts` 已传 `session_id`。多轮对话基础能力已存在，不是从 0 到 1。

**待优化**：
- Token 计数估算：当前固定截取最近 10 轮，不考虑 token 总量。长消息场景下可能超模型上限，短消息场景下浪费上下文窗口
- 窗口策略可配置：不同模型上下文窗口不同（DeepSeek 64k vs GPT-4 128k），应根据模型动态调整
- 工作流场景的上下文：当前工作流执行（`workflow_nodes.py`）的 LLM 节点不带对话历史，只有 system + user 两条消息

**方案**：
- 引入 `tiktoken` 或简单字符数估算，按模型 max_tokens 的 70% 作为历史上限
- `MAX_HISTORY_MESSAGES` 改为动态计算（按 token 预算裁剪，而非固定条数）
- 工作流 LLM 节点可选是否继承对话上下文

**涉及文件**：`chat.py`, `workflow_nodes.py`, `config.py`

### 1.2 多模型抽象

**现状**：硬编码 DeepSeek（`llm.py`）。

**方案**：
- 统一 `ModelProvider` 接口，所有提供商走 OpenAI 兼容 API 格式
- `.env` 配置多个 provider（api_key + base_url + model_name）
- 前端设置页选择默认模型，工作流 LLM 节点可选模型
- 第一批支持：DeepSeek / OpenAI / 通义千问（都兼容 OpenAI 格式，改动最小）

**为什么放 Phase 1**：这是后续所有功能的底层依赖。工作流节点扩展、Skill 执行、聊天都依赖模型抽象层。先统一接口，后面不用返工。

**涉及文件**：`llm.py`（重构）, `config.py`, `workflow_nodes.py`, 新增设置页

### 1.3 PDF 文档支持

**现状**：`rag.py:97-98` 只支持 `.txt` / `.md`。知识库问答场景跑不通。

**方案**：
- 引入 `pymupdf`（轻量，纯 Python，不引入重依赖）
- `load_document` 按后缀分发解析器
- 同时支持 DOCX（`python-docx`）
- 不做高级 PDF 解析（布局/表格/公式），那是 Phase 4 的事

**涉及文件**：`rag.py`, `knowledge/processor.py`, `useKnowledgeApi.ts`, `pyproject.toml`

### 1.4 安全闸门（P1 出口条件，不过不放行）

**为什么是闸门不是"底线"**：v2 说"安全底线"还是太软。这三件套是 P2 的前置条件，缺一不可。后面每做一个功能都在调 LLM API（花钱）、暴露新攻击面，没有限流和审计就是蒙眼飙车。

**三件套**：

1. **Rate limiting**（`slowapi` 中间件）
   - LLM 端点：10 req/min/user
   - 其他端点：60 req/min/user
   - 全局：1000 req/min（防 DDoS）
   - 验收：超过限额后返回 ≥1 个 429，且 response header 含 `Retry-After` 和 `X-RateLimit-Limit` 字段

2. **审计日志**
   - 关键操作写结构化日志：创建/删除工作流、上传/删除文档、执行工作流、登录/登出
   - 格式：JSON Lines，每条必含 `timestamp` / `user_id` / `action` / `resource_id` / `ip` 五个字段
   - 验收：自动化脚本校验日志文件最近 N 条记录的结构化字段完整性（缺字段则 CI 失败）

3. **Token 计量**
   - 每次 LLM 调用记录：model / input_tokens / output_tokens / user_id / timestamp
   - 写日志文件（不需要 UI，Phase 3 再做仪表盘）
   - 验收：跑 10 次聊天后，日志中有 10 条 token 记录，每条 input_tokens > 0 且 output_tokens > 0

**附加安全项**（同步做，但不作为闸门条件）：
- 登录失败限制：5 次失败锁定 15 分钟
- 错误信息脱敏：内部异常用通用消息返回，`str(e)` 只写日志

**前置依赖**：`pyproject.toml` 需新增 `pytest-cov`，建立覆盖率管道（当前只有 pytest，无 coverage 工具）。

**涉及文件**：新增 `middleware/rate_limit.py`, `middleware/audit.py`, `llm.py`（token 计量）, `auth.py`, `pyproject.toml`

### 1.5 ChromaDB 异步化

**ChromaDB**：所有同步操作用 `asyncio.to_thread()` 包装。

**路由守卫 hydration 竞态（降级为回归验证项）**：`main.ts:20` 已 `await authStore.init()` 在 `app.use(router)` 之前，主流程已规避。仅需回归验证：刷新各页面确认不会错误跳转 `/login`。不作为 P1 主任务。

**涉及文件**：`chroma_client.py`, `rag.py`

---

## 五、Phase 2 — 实用（第 3-5 月）

> 按能力栈依赖图推进：先统一工作流 schema → 再扩展节点 → 最后上发布能力。

**北极星指标**：周活工作流数 ≥ 20，工作流成功执行率 ≥ 95%。

**DOD（验收标准）**：
- 工作流支持代码节点和 HTTP 节点
- 知识库混合检索 + Rerank 可用
- 工作流可导出 JSON / 可导入
- 至少 1 种嵌入/发布方式可用（iframe 或 OpenAI 兼容 API）
- 并发 50 用户下 P95 延迟 < 3s（不含 LLM 推理）
- 错误率 < 1%

**Kill List（本阶段不做）**：
- 不做多条件分支（当前 true/false 够用，复杂逻辑用代码节点替代）
- 不做工作流调试模式（日志已经够用）
- 不做简单模式 / 模板库（先让高级模式跑顺）
- 不做存储层迁移（Phase 3 的事）

### 2.1 工作流 Schema 统一（前置依赖）

**为什么先做这个**：当前 `GraphData` 的 nodes/edges 都是 `Dict[str, Any]`，前后端没有类型约束。后面加节点类型会不断返工。

**方案**：
- 后端：定义 `NodeSchema`（Pydantic discriminated union），每种节点类型有明确的 data schema
- 前端：对应 TypeScript interface，`GraphData` 从 `any` 改为 union type
- 工作流导出/导入的 JSON schema 同步定义
- 这一步不改功能，只加类型约束

**涉及文件**：`models/workflow.py`, `frontend/src/types/`

### 2.2 代码执行节点

**安全前提**：RestrictedPython 官方明确声明"不是 sandbox"，且 2024-2025 连续有安全修复/CVE。仅 AST 检查 + 超时不够。

**方案**：
- **默认关闭 + feature flag**：`ENABLE_CODE_NODE=false`，运行时可通过 API 一键熔断（见 2.7 功能熔断）
- **可信环境开关**：开启时弹出安全警告，明确告知"仅在可信环境中使用"
- **隔离措施（多层，定位：降低误用风险，不是安全隔离）**：
  - 低权限运行用户：subprocess 以 `nobody` 或专用低权限用户执行
  - `shell=False`（显式禁用 shell 注入）
  - 环境变量白名单：只传入上游节点输出，清除 PATH/HOME/USER 等系统变量
  - 超时 30s + 内存限制（`resource.setrlimit` RLIMIT_AS 256MB）
  - 临时目录隔离 + 执行后清理
  - 输出大小限制（stdout 截断到 10KB）
  - 导入模块 AST 预扫描：拒绝 `os.system`/`subprocess`/`socket`/`shutil`/`ctypes`（自写 AST visitor，不依赖 RestrictedPython）
  - **明确定位**：AST 白名单是"降低误用"而非"安全隔离"，不能防住恶意用户的刻意绕过。文档和 UI 必须标注"仅限可信环境使用，不提供沙箱级安全保证"
- **不做独立沙箱服务**（守住轻量级边界），但文档明确标注安全边界和适用场景
- 输入：上游节点输出通过环境变量传入；输出：stdout 作为节点输出

**涉及文件**：`workflow_nodes.py`, `workflow_engine.py`, `config.py`, 新增 `CodeNode.vue`, 新增 `utils/code_sandbox.py`

### 2.3 HTTP 请求节点

**安全前提**：仅靠内网网段黑名单不够（DNS 重绑定、IPv6、HTTP 跳转、环境代理变量都能绕过）。

**方案**：
- **默认关闭 + feature flag**：`ENABLE_HTTP_NODE=false`，运行时可一键熔断
- **SSRF 防护（六层）**：
  1. Scheme 白名单：只允许 `http://` 和 `https://`（禁止 `file://`、`ftp://`、`gopher://` 等）
  2. URL 解析后检查 IP，拦截以下网段：
     - IPv4: `0.0.0.0/8`, `10.0.0.0/8`, `100.64.0.0/10`(CGN), `127.0.0.0/8`, `169.254.0.0/16`(link-local), `172.16.0.0/12`, `192.168.0.0/16`, `198.18.0.0/15`(benchmark), `224.0.0.0/4`(multicast)
     - IPv6: `::1`, `fc00::/7`(ULA), `fe80::/10`(link-local), `ff00::/8`(multicast)
  3. DNS 解析后再次检查 IP（防 DNS 重绑定）
  4. 禁止 HTTP 跳转（`allow_redirects=False`），或跳转后重新检查目标 IP
  5. HTTP client 设置 `trust_env=False`（防止读取环境代理变量 `HTTP_PROXY` 等）
  6. 可选 URL 白名单模式（管理员配置允许访问的域名列表）
- 支持 GET/POST/PUT/DELETE，URL 支持 `{{variable}}` 插值
- 响应支持 JSON path 提取
- 超时 10s，响应体截断到 1MB

**涉及文件**：`workflow_nodes.py`, `config.py`, 新增 `HttpNode.vue`, 新增 `utils/ssrf_guard.py`

### 2.4 混合检索 + Rerank

**方案**（分三步，可独立交付）：
1. ChromaDB 切换 cosine 距离（替代 L2，1 天）
2. SQLite FTS5 全文检索 + 向量检索结果合并（3 天）
3. SiliconFlow Rerank API 集成（2 天）

**涉及文件**：`rag.py`, `chroma_client.py`, `KnowledgeView.vue`

### 2.5 工作流导出/导入

**方案**：
- 导出：序列化为 JSON（基于 2.1 定义的 schema），提供下载
- 导入：上传 JSON，schema 验证后创建工作流
- 预置 2 个模板：知识库问答助手、SOP 执行助手（锚定场景的标准实现）

**涉及文件**：`workflow.py`（API）, `WorkflowEditor.vue`

### 2.6 嵌入与 API 发布（最小可行版）

**方案**：
- **iframe 嵌入**：生成带 token 的公开聊天页面 URL，可 iframe 嵌入
- **OpenAI 兼容 API**：`/api/v1/openai/chat/completions`，让工作流可被任何 OpenAI 客户端调用
- 不做多渠道（微信/飞书/钉钉），那是平台化的活

**涉及文件**：新增 `openai_compat.py`, 新增公开聊天页面

### 2.7 功能熔断机制（P2 基础设施）

**为什么需要**：P2 新增的代码节点和 HTTP 节点是高风险能力，上线后如果出安全事故，必须能在不重启、不发版的情况下秒级关闭。

**方案**：
- 所有 P2 新能力通过 feature flag 控制，默认关闭
- Feature flag 存储在 DB（`settings` 表），管理员可通过 API 或前端设置页运行时切换
- 关键 flag：`ENABLE_CODE_NODE`、`ENABLE_HTTP_NODE`、`ENABLE_OPENAI_API`、`ENABLE_PUBLIC_EMBED`
- 工作流引擎执行节点前检查 flag，flag 关闭时节点返回 `node_error`（"此功能已被管理员禁用"）
- 前端节点面板根据 flag 显示/隐藏对应节点类型

**验收**：管理员关闭 `ENABLE_CODE_NODE` 后，已有工作流中的代码节点执行时立即返回错误，无需重启服务。

**涉及文件**：`config.py`, `workflow_engine.py`, `workflow_nodes.py`, 新增 `api/settings.py`

---

## 六、Phase 3 — 稳定（第 6-8 月）

> 还技术债，让代码可维护、系统可观测。

**北极星指标**：P95 延迟下降 30%，测试覆盖率 ≥ 70%，线上错误率 < 0.5%。

**DOD（验收标准）**：
- Session/Workflow 全部迁移到 SQLAlchemy + Alembic
- SSE 代码前后端各只有一份实现
- Token 消耗有 UI 仪表盘
- 后端测试 ≥ 80 个，覆盖率 ≥ 70%（需先在 `pyproject.toml` 加 `pytest-cov`，当前无覆盖率管道）
- 前端 E2E 覆盖核心路径
- 并发 100 用户下系统稳定

**Kill List（本阶段不做）**：
- 不做新功能（纯还债 + 可观测性）
- 不做架构大重构（不换框架、不拆服务）

### 3.1 存储层统一迁移

**方案**：
- Session / Workflow 从 JSON 文件迁移到 SQLAlchemy
- 引入 Alembic 替代手动 `PRAGMA table_info` 迁移
- Session 过期清理（默认 30 天）
- Skill 元数据入库，SKILL.md 仅作导入/导出格式

**涉及文件**：`database.py`, `chat_session.py`, `workflow.py`, `models/`

### 3.2 代码去重与重构

**后端**：
- SSE 事件解析抽取公共函数（`chat_stream.py` 中重复逻辑）
- `chat_stream.py` 拆分职责（skill 流/chat 流/workflow 流分离，session 保存由调用方统一处理）
- `skill_executor.py` 移除 dict 兼容死代码
- SkillLoader 统一为单例
- 核心模块改用 FastAPI `Depends` 注入（替代 `lru_cache` 单例）

**前端**：
- `useChatSSE` 复用 `useSSEStream`（消除 `readErrorDetail`/`handle401` 重复）
- `alert()` 替换为 Toast 组件
- User 类型定义统一
- SSE 事件数据从 `Record<string, unknown>` 改为具体 interface
- WorkflowEditor `elements` 延迟初始化
- ChatTerminal 的 `loadWorkflows`/`loadKnowledgeBases` 提取到 composable

### 3.3 可观测性

**方案**：
- Token 消耗仪表盘（基于 Phase 1 的日志数据，新增前端 UI）
- 工作流执行日志持久化到 DB（当前只在内存中）
- 对话质量反馈（点赞/点踩）
- 请求日志结构化（method / path / status / duration / user_id）

### 3.4 测试补全

- RAG Pipeline 集成测试（文档处理 → 分块 → embedding → 检索）
- Workflow 条件分支边界测试
- SSE 解析器 chunk 边界测试
- Embedding 批量分片测试
- 前端 E2E（Playwright）覆盖：登录 → 创建知识库 → 上传文档 → 聊天问答 → 创建工作流 → 运行

---

## 七、Phase 4 — 验证后决策（第 9-12 月）

> 不预设方向，根据前三个阶段的数据决定。

### 决策树

```
留存数据如何？
├── 周活用户 ≥ 50，留存 ≥ 30%
│   ├── 用户主要用知识库场景 → 深耕 RAG（高级 PDF 解析、QA 标注、多库混合）
│   ├── 用户主要用工作流场景 → 深耕工作流（多条件分支、异常处理、调试模式）
│   └── 两者都用 → 做简单模式降低门槛 + 更多模板
├── 周活用户 10-50，留存 < 30%
│   ├── 分析流失原因
│   ├── 如果是"功能不够" → 补最高频需求
│   └── 如果是"太复杂" → 做简单模式 + 引导流程
└── 周活用户 < 10
    ├── 重新审视定位
    └── 考虑 pivot 或聚焦单一场景
```

### 候选方向（按数据决定是否启动）

| 方向 | 启动条件 | 内容 |
|------|---------|------|
| RAG 深耕 | 知识库场景留存 ≥ 40% | Marker PDF 解析、QA 标注、多库混合检索 |
| 工作流深耕 | 工作流场景留存 ≥ 40% | 多条件分支、异常处理、调试模式、工作流版本管理 |
| 简单模式 | 新用户 3 日留存 < 20% | 填空式配置 + 模板库 + 引导流程 |
| MCP Client | 有明确用户需求 | 工作流中调用外部 MCP Server 工具 |
| 工作流异常处理 | 工作流失败率 > 5% | 节点超时/重试/降级分支 |

---

## 八、技术债清单（按阶段分配）

| # | 问题 | 位置 | Phase |
|---|------|------|-------|
| 1 | ChromaDB 同步调用阻塞事件循环 | `chroma_client.py` | 1 |
| 2 | 路由守卫 hydration 竞态（已被 main.ts:20 规避，降级为回归验证） | `router/index.ts` | 1（验证） |
| 3 | 无 rate limiting | 全部 API | 1 |
| 4 | 无登录失败限制 | `auth.py` | 1 |
| 5 | 错误信息泄露 | `knowledge.py:175` 等 | 1 |
| 6 | Embedding 批量无分片 | `rag.py:75` | 2 |
| 7 | Session/Workflow JSON 文件存储 | `data/` 目录 | 3 |
| 8 | 手动数据库迁移 | `database.py:41-44` | 3 |
| 9 | SSE 代码重复（前后端） | 多处 | 3 |
| 10 | `lru_cache` 全局单例 | `rag.py`, `llm.py` 等 | 3 |
| 11 | `skill_executor.py` dict 兼容死代码 | `skill_executor.py:131-144` | 3 |
| 12 | SkillLoader 重复实例化 | `workflow_nodes.py:53,220` | 3 |
| 13 | `alert()` 错误提示 | 前端多处 | 3 |
| 14 | User 类型重复定义 | `stores/auth.ts`, `types/index.ts` | 3 |
| 15 | Session 文件无清理机制 | `data/sessions/` | 3 |

---

## 九、竞品功能对照矩阵

| 功能 | Agent Flow Lite | Dify | Flowise | LangFlow | Coze | FastGPT |
|------|:-:|:-:|:-:|:-:|:-:|:-:|
| 可视化工作流 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 多模型支持 | ❌→P1 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 多轮对话 | ⚠️→P1 优化 | ✅ | ✅ | ✅ | ✅ | ✅ |
| PDF/DOCX 支持 | ❌→P1 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 代码执行节点 | ❌→P2 | ✅ | ✅ | ✅ | ✅ | ✅ |
| HTTP 请求节点 | ❌→P2 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 混合检索+Rerank | ❌→P2 | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ |
| 工作流导出/导入 | ❌→P2 | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| API 发布 | ❌→P2 | ✅ | ✅ | ✅ | ✅ | ✅ |
| SSE 流式输出 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| RAG 知识库 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Skill 系统 | ✅ | ⚠️ | ❌ | ❌ | ⚠️ | ❌ |
| 轻量级部署 | ✅ | ❌ | ✅ | ✅ | ❌ | ⚠️ |
| Rate Limiting | ❌→P1 | ✅ | ✅ | ⚠️ | ✅ | ⚠️ |
| Token 追踪 | ❌→P1 | ✅ | ⚠️ | ⚠️ | ✅ | ✅ |

✅ 完整支持 ⚠️ 部分支持 ❌ 不支持 →Pn 计划在第 n 阶段实现

---

## 十、参考资源

- **Dify**: [github.com/langgenius/dify](https://github.com/langgenius/dify) — 67k+ stars，微服务架构参考
- **LangFlow**: [github.com/langflow-ai/langflow](https://github.com/langflow-ai/langflow) — 145k stars，Python + React Flow
- **Flowise**: [github.com/FlowiseAI/Flowise](https://github.com/FlowiseAI/Flowise) — 49k stars，Node.js + LangGraph
- **Coze Studio**: [github.com/coze-dev/coze-studio](https://github.com/coze-dev/coze-studio) — Go + React，Apache 2.0，可参考源码
- **FastGPT**: [github.com/labring/FastGPT](https://github.com/labring/FastGPT) — 27k stars，知识库做得最深
