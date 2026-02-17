# P3 训练动作清单 v3

> 基于代码现状核实 + 两轮 review 后定稿。T1 拆成独立回滚的 a/b 两步，验证标准为可执行脚本。

---

## 任务总览

| # | 任务 | 训练目标 | 体量 |
|---|------|----------|------|
| T1a | Session 存储迁移 | 架构：async ORM、事务边界 | 中 |
| T1b | Workflow 存储迁移 | 架构：单文件→多行、迁移脚本幂等性 | 中 |
| T2 | 覆盖率可见化 | 工程习惯：先看见再设门槛 | 轻 |
| T3 | Alembic 收尾 | 收尾：删遗留、统一入口 | 轻 |

已砍掉：
- ~~SSE 去重~~：`app/utils/sse.py` 已存在，三个 API 已统一调用。

---

## T1a：Session 存储迁移

### 现状
- `app/api/chat_session.py:13` filelock + `data/sessions/{id}.json`
- 每个 session 一个文件，filelock 按文件粒度

### 动作
1. 新建 `app/models/session.py`：ChatSession ORM model（id, user_id, title, messages JSON, created_at, updated_at）
2. Alembic 生成迁移文件
3. 重写 `chat_session.py`：所有 CRUD 改为 async SQLAlchemy
4. 删除该模块的 filelock 引用

### 验证
```bash
cd backend && bash scripts/verify_t1a.sh
```
脚本检查：JSON 文件数 == DB 记录数 → 抽样 ID 匹配 → 幂等性（二次执行 COUNT 不变）→ `uv run pytest` 全绿。

### 回滚点
T1a 完成后 commit。T1b 翻车不影响 Session 迁移。

---

## T1b：Workflow 存储迁移

### 现状
- `app/api/workflow.py:16` filelock + `data/workflows.json` 单文件存所有工作流
- 全局互斥锁，一个人写所有人等

### 动作
1. 新建 `app/models/workflow.py`：Workflow ORM model（id, user_id, name, description, graph_data JSON, created_at, updated_at）
2. Alembic 生成迁移文件
3. 重写 `workflow.py` 存储层
4. 写迁移脚本 `scripts/migrate_workflows_to_db.py`（幂等）
5. 删除该模块的 filelock 引用

### 验证
```bash
cd backend && bash scripts/verify_t1b.sh
```
脚本检查：JSON 工作流数（兼容 dict/list 两种格式）== DB 记录数 → 抽样 name 匹配 → 幂等性 → `uv run pytest` 全绿。

### 回滚点
T1b 完成后 commit。T1a 和 T1b 互不依赖。

---

## T2：覆盖率可见化（与 T1a 并行）

### 现状
- `pytest-cov` 已在依赖中，未配置
- CI 无 coverage step

### 动作
1. `pyproject.toml` 加 pytest-cov 配置
2. 跑一次 `uv run pytest --cov=app --cov-report=term-missing`，记录基线
3. `.github/workflows/quality-gate.yml` 加 coverage report step（只上报不阻断）
4. 看报告，识别 3 个最关键的未覆盖模块，补 5-10 条测试
5. 门槛留到下个迭代设

### 验证
```bash
cd backend && uv run pytest --cov=app --cov-report=term-missing -q
```

---

## T3：Alembic 收尾

### 现状
- `alembic.ini`、`alembic/env.py` 已存在
- `database.py:41-44` 仍有 PRAGMA 手动迁移
- T1a/T1b 的新 models 需要纳入 alembic 管理

### 动作
1. 确认 autogenerate 能检测到 T1a/T1b 新增的 models
2. 删除 `database.py` 中 PRAGMA table_info 代码
3. 确认启动路径：lifespan → alembic upgrade head → 正常运行

### 验证
```bash
cd backend && bash scripts/verify_t3.sh
```
脚本检查：删库 → `alembic upgrade head` → 验证 users/auth_tokens/chat_sessions/workflows 表全部存在 → `uv run pytest` 全绿 → 恢复备份。

---

## 执行顺序

```
S1: T1a（Session 迁移）+ T2（覆盖率基线）  →  commit
S2: T1b（Workflow 迁移 + 幂等脚本）         →  commit
S3: T3（Alembic 收尾）+ 全量回归 + 复盘     →  commit
```

3 个 session，每个有独立 commit 作为回滚点。

---

## 复盘模板

每个任务完成后回答：
1. 哪里卡了？为什么？
2. 重来一次会怎么做不同？
3. 练到了什么能力？
