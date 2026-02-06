# Skill 系统技术设计文档

> 版本: 1.0
> 日期: 2026-02-04
> 状态: 待开发

## 1. 概述

### 1.1 背景

基于 [Agent Skills](https://agentskills.io/) 开放标准，为 Agent Flow Lite 添加 Skill 功能。Skill 是可复用的 prompt 模板，支持变量输入、知识库关联，可在工作流和 Chat 中使用。

### 1.2 设计原则

- **兼容开放标准**：基于 Agent Skills 规范扩展，保持 SKILL.md 格式兼容性
- **文件即配置**：Skill 以文件夹形式存储，用户可直接编辑、git 管理
- **渐进式披露**：元数据轻量加载，完整内容按需加载
- **MVP 优先**：先跑通核心流程，AI 辅助创建等高级功能后续迭代

### 1.3 功能范围

| 功能 | 优先级 | 说明 |
|------|--------|------|
| Skill CRUD API | P0 | 创建、读取、更新、删除 |
| Skill 列表页面 | P0 | 展示所有 skill，支持预览 |
| Skill 编辑器 | P0 | 编辑 SKILL.md 文件 |
| Skill 独立执行 | P0 | 在 Skill 页面测试运行 |
| 工作流 Skill 节点 | P0 | 在工作流中使用 skill |
| Chat @skill 调用 | P1 | 在对话中通过 @name 调用 |
| LLM 节点加载 Skill | P1 | LLM 节点可从 skill 加载配置 |
| AI 辅助创建 Skill | P2 | 弹窗对话引导生成 skill |

## 2. 数据模型

### 2.1 文件结构

```
/skills/                           # 项目根目录下
├── article-summary/
│   ├── SKILL.md                   # 必需：skill 定义
│   ├── scripts/                   # 可选：可执行脚本
│   ├── references/                # 可选：参考文档
│   └── assets/                    # 可选：静态资源
├── code-review/
│   └── SKILL.md
└── meeting-notes/
    └── SKILL.md
```

### 2.2 SKILL.md 格式

采用 YAML frontmatter + Markdown 正文格式，基于 Agent Skills 标准扩展。

```markdown
---
# === 标准字段（Agent Skills 规范） ===
name: article-summary
description: 将长文章压缩成结构化要点。适用于新闻、论文、报告等长文本的快速提炼。
license: MIT
metadata:
  author: your-name
  version: "1.0"

# === 扩展字段（Agent Flow Lite 特有） ===
inputs:
  - name: article
    label: 文章内容
    type: textarea
    required: true
    description: 需要总结的文章全文
  - name: style
    label: 摘要风格
    type: text
    required: false
    default: 简洁专业

knowledge_base: null              # 关联知识库的 ID 或 name，可选

model:
  temperature: 0.3
  max_tokens: 2000

user_id: null                     # 预留用户隔离字段
---

请将以下文章总结为 {{style}} 的要点：

{{article}}

## 输出要求

- 提取 3-5 个核心观点
- 每个观点用一句话概括
- 保留关键数据和引用

## 注意事项

- 如果文章包含多个主题，按主题分组输出
- 保持客观中立，不添加个人评价
```

### 2.3 字段定义

#### 标准字段（Agent Skills 规范）

| 字段 | 必需 | 类型 | 约束 |
|------|------|------|------|
| `name` | 是 | string | 1-64字符，小写字母/数字/连字符，不能以连字符开头结尾，需与文件夹名一致 |
| `description` | 是 | string | 1-1024字符，描述 skill 功能和使用场景 |
| `license` | 否 | string | 许可证名称 |
| `metadata` | 否 | object | 任意键值对，用于扩展元数据 |
| `compatibility` | 否 | string | 环境要求说明 |
| `allowed-tools` | 否 | string | 预授权工具列表（实验性） |

#### 扩展字段（Agent Flow Lite 特有）

| 字段 | 必需 | 类型 | 说明 |
|------|------|------|------|
| `inputs` | 否 | array | 输入变量定义列表 |
| `inputs[].name` | 是 | string | 变量名，用于 prompt 中的 `{{name}}` 引用 |
| `inputs[].label` | 是 | string | UI 显示标签 |
| `inputs[].type` | 是 | string | 类型：`text` \| `textarea` |
| `inputs[].required` | 否 | boolean | 是否必填，默认 false |
| `inputs[].default` | 否 | string | 默认值 |
| `inputs[].description` | 否 | string | 输入说明 |
| `knowledge_base` | 否 | string | 关联知识库 ID 或 name |
| `model` | 否 | object | 模型配置 |
| `model.temperature` | 否 | number | 温度参数，0-2 |
| `model.max_tokens` | 否 | number | 最大输出 token 数 |
| `user_id` | 否 | string | 预留用户隔离字段 |

### 2.4 变量语法

Prompt 正文中使用 `{{variable}}` 语法引用输入变量：

```markdown
请将以下文章总结为 {{style}} 的要点：

{{article}}
```

变量替换在执行时进行，未提供的可选变量使用默认值或空字符串。

## 3. API 设计

### 3.1 路由定义

基础路径：`/api/v1/skills`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/skills` | 列出所有 skill |
| GET | `/api/v1/skills/{name}` | 获取单个 skill 详情 |
| POST | `/api/v1/skills` | 创建新 skill |
| PUT | `/api/v1/skills/{name}` | 更新 skill |
| DELETE | `/api/v1/skills/{name}` | 删除 skill |
| POST | `/api/v1/skills/{name}/run` | 执行 skill |

### 3.2 数据结构

#### SkillSummary（列表用）

```python
class SkillSummary(BaseModel):
    name: str
    description: str
    has_inputs: bool
    has_knowledge_base: bool
    updated_at: datetime
```

#### SkillDetail（详情用）

```python
class SkillDetail(BaseModel):
    name: str
    description: str
    license: Optional[str]
    metadata: Optional[Dict[str, str]]
    inputs: Optional[List[SkillInput]]
    knowledge_base: Optional[str]
    model: Optional[SkillModelConfig]
    prompt: str  # Markdown 正文
    raw_content: str  # 完整 SKILL.md 内容
    created_at: datetime
    updated_at: datetime

class SkillInput(BaseModel):
    name: str
    label: str
    type: Literal["text", "textarea"]
    required: bool = False
    default: Optional[str] = None
    description: Optional[str] = None

class SkillModelConfig(BaseModel):
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000
```

#### SkillCreateRequest

```python
class SkillCreateRequest(BaseModel):
    name: str  # 同时作为文件夹名
    content: str  # 完整 SKILL.md 内容
```

#### SkillRunRequest

```python
class SkillRunRequest(BaseModel):
    inputs: Dict[str, str]  # 变量名 -> 值
```

#### SkillRunResponse（SSE 流式）

```python
# SSE 事件类型
event: thought    # RAG 检索过程
data: {"content": "正在检索相关文档..."}

event: token      # LLM 输出 token
data: {"content": "这是"}

event: citation   # 引用来源
data: {"sources": [...]}

event: done       # 完成
data: {"usage": {...}}
```

### 3.3 API 详细说明

#### GET /api/v1/skills

列出所有 skill 的摘要信息。

**响应示例：**
```json
{
  "skills": [
    {
      "name": "article-summary",
      "description": "将长文章压缩成结构化要点",
      "has_inputs": true,
      "has_knowledge_base": false,
      "updated_at": "2026-02-04T10:00:00Z"
    }
  ]
}
```

#### GET /api/v1/skills/{name}

获取单个 skill 的完整信息。

**响应示例：**
```json
{
  "name": "article-summary",
  "description": "将长文章压缩成结构化要点",
  "inputs": [
    {
      "name": "article",
      "label": "文章内容",
      "type": "textarea",
      "required": true
    }
  ],
  "knowledge_base": null,
  "model": {
    "temperature": 0.3,
    "max_tokens": 2000
  },
  "prompt": "请将以下文章总结为 {{style}} 的要点：\n\n{{article}}\n\n## 输出要求\n...",
  "raw_content": "---\nname: article-summary\n..."
}
```

#### POST /api/v1/skills

创建新 skill。

**请求体：**
```json
{
  "name": "code-review",
  "content": "---\nname: code-review\ndescription: 审查代码质量\n---\n\n请审查以下代码：\n\n{{code}}"
}
```

#### POST /api/v1/skills/{name}/run

执行 skill，返回 SSE 流。

**请求体：**
```json
{
  "inputs": {
    "article": "这是一篇很长的文章...",
    "style": "学术风格"
  }
}
```

**响应：** SSE 流，格式同 Chat API。

## 4. 后端实现

### 4.1 文件结构

```
backend/
├── app/
│   ├── api/
│   │   └── skill.py              # Skill API 路由
│   ├── core/
│   │   ├── skill_loader.py       # SKILL.md 解析和文件操作
│   │   └── skill_executor.py     # Skill 执行逻辑
│   └── models/
│       └── skill.py              # Pydantic 数据模型
└── main.py                       # 注册 skill router
```

### 4.2 核心模块

#### skill_loader.py

职责：
- 扫描 `/skills/` 目录，发现所有 skill
- 解析 SKILL.md 文件（YAML frontmatter + Markdown）
- 提供文件读写操作

```python
class SkillLoader:
    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir

    def list_skills(self) -> List[SkillSummary]:
        """扫描目录，返回所有 skill 摘要"""
        pass

    def get_skill(self, name: str) -> SkillDetail:
        """读取并解析单个 skill"""
        pass

    def create_skill(self, name: str, content: str) -> SkillDetail:
        """创建 skill 文件夹和 SKILL.md"""
        pass

    def update_skill(self, name: str, content: str) -> SkillDetail:
        """更新 SKILL.md 内容"""
        pass

    def delete_skill(self, name: str) -> None:
        """删除 skill 文件夹"""
        pass

    def parse_skill_md(self, content: str) -> Tuple[dict, str]:
        """解析 SKILL.md，返回 (frontmatter, body)"""
        pass
```

#### skill_executor.py

职责：
- 变量替换（`{{variable}}` → 实际值）
- RAG 增强（如果配置了 knowledge_base）
- 调用 LLM 生成响应
- 流式输出 SSE 事件

```python
class SkillExecutor:
    def __init__(self, rag_pipeline: RAGPipeline, llm_client: LLMClient):
        self.rag = rag_pipeline
        self.llm = llm_client

    async def execute(
        self,
        skill: SkillDetail,
        inputs: Dict[str, str]
    ) -> AsyncGenerator[str, None]:
        """
        执行 skill，返回 SSE 事件流

        1. 验证必填 inputs
        2. 替换 prompt 中的变量
        3. 如果有 knowledge_base，执行 RAG 检索
        4. 调用 LLM 生成响应
        5. yield SSE 事件
        """
        pass

    def _replace_variables(self, prompt: str, inputs: Dict[str, str], defaults: Dict[str, str]) -> str:
        """替换 {{variable}} 为实际值"""
        pass
```

### 4.3 工作流集成

在 `workflow_nodes.py` 中添加 skill 节点执行器：

```python
async def execute_skill_node(
    node: WorkflowNode,
    context: ExecutionContext,
    skill_loader: SkillLoader,
    skill_executor: SkillExecutor
) -> AsyncGenerator[StreamEvent, None]:
    """
    执行 skill 节点

    node.data 结构：
    {
        "skill_name": "article-summary",
        "input_mapping": {
            "article": "{{step1.output}}",  # 从上游节点获取
            "style": "简洁"                  # 固定值
        }
    }
    """
    skill = skill_loader.get_skill(node.data["skill_name"])

    # 解析 input_mapping，替换上游变量
    inputs = {}
    for key, value in node.data["input_mapping"].items():
        inputs[key] = context.resolve_variable(value)

    # 执行 skill
    async for event in skill_executor.execute(skill, inputs):
        yield event
```

### 4.4 Chat @skill 集成

在 `chat.py` 中添加 @skill 解析逻辑：

```python
def parse_at_skill(message: str) -> Tuple[Optional[str], str]:
    """
    解析消息中的 @skill 调用

    输入: "@article-summary 这是一篇文章..."
    输出: ("article-summary", "这是一篇文章...")

    输入: "普通消息"
    输出: (None, "普通消息")
    """
    pattern = r'^@([a-z0-9-]+)\s+(.+)$'
    match = re.match(pattern, message, re.DOTALL)
    if match:
        return match.group(1), match.group(2)
    return None, message
```

当检测到 @skill 调用时：
1. 加载对应 skill
2. 将剩余消息作为第一个 required input 的值
3. 执行 skill 并流式返回

## 5. 前端实现

### 5.1 文件结构

```
frontend/src/
├── views/
│   ├── SkillsView.vue            # Skill 列表页
│   └── SkillEditor.vue           # Skill 编辑页
├── components/
│   └── nodes/
│       └── SkillNode.vue         # 工作流 Skill 节点
├── router/
│   └── index.ts                  # 添加 /skills 路由
└── App.vue                       # 导航添加 Skills
```

### 5.2 路由配置

```typescript
// router/index.ts
{
  path: '/skills',
  name: 'skills',
  component: () => import('@/views/SkillsView.vue')
},
{
  path: '/skills/:name',
  name: 'skill-editor',
  component: () => import('@/views/SkillEditor.vue')
},
{
  path: '/skills/new',
  name: 'skill-new',
  component: () => import('@/views/SkillEditor.vue')
}
```

### 5.3 SkillsView.vue

功能：
- 展示所有 skill 卡片列表
- 显示 name、description、inputs 数量、是否关联知识库
- 点击卡片进入编辑页
- "新建 Skill" 按钮
- 每个卡片有"运行"按钮，弹窗填写 inputs 后执行

### 5.4 SkillEditor.vue

功能：
- 左侧：SKILL.md 文本编辑器（Monaco Editor 或 CodeMirror）
- 右侧：实时预览解析结果
  - 显示 name、description
  - 显示 inputs 列表
  - 显示 prompt 预览
- 顶部工具栏：保存、删除、运行测试
- 底部：运行测试面板，填写 inputs 后执行

### 5.5 SkillNode.vue

工作流中的 Skill 节点组件：

```vue
<template>
  <BaseNode :node="node" color="purple">
    <div class="skill-node">
      <div class="skill-select">
        <select v-model="selectedSkill">
          <option v-for="skill in skills" :key="skill.name" :value="skill.name">
            {{ skill.name }}
          </option>
        </select>
      </div>

      <!-- 输入映射配置 -->
      <div class="input-mapping" v-if="skillDetail">
        <div v-for="input in skillDetail.inputs" :key="input.name" class="mapping-row">
          <label>{{ input.label }}</label>
          <input
            v-model="inputMapping[input.name]"
            :placeholder="input.required ? '必填' : input.default || '可选'"
          />
        </div>
      </div>
    </div>
  </BaseNode>
</template>
```

节点数据结构：
```typescript
interface SkillNodeData {
  skill_name: string
  input_mapping: Record<string, string>  // 变量名 -> 值或上游引用
}
```

### 5.6 Chat @skill 支持

在 ChatTerminal.vue 中：
- 输入框监听 `@` 字符，弹出 skill 列表提示
- 选择 skill 后自动补全 `@skill-name `
- 发送时检测 @skill 前缀，调用对应 API

## 6. 执行流程

### 6.1 独立执行流程

```
用户点击"运行" → 弹窗填写 inputs → 点击"执行"
    ↓
POST /api/v1/skills/{name}/run { inputs: {...} }
    ↓
SkillExecutor.execute()
    ├── 验证必填 inputs
    ├── 替换 {{variable}} → 实际值
    ├── [可选] RAG 检索 → yield thought 事件
    ├── 构建 messages: [{ role: "user", content: 替换后的 prompt }]
    ├── LLM 流式生成 → yield token 事件
    └── 完成 → yield done 事件
    ↓
前端 SSE 接收，实时显示输出
```

### 6.2 工作流执行流程

```
工作流到达 Skill 节点
    ↓
WorkflowEngine._execute_node() → execute_skill_node()
    ↓
解析 input_mapping
    ├── 固定值："简洁" → "简洁"
    └── 上游引用："{{step1.output}}" → context.resolve_variable() → 实际值
    ↓
SkillExecutor.execute(skill, resolved_inputs)
    ↓
yield 事件流 → 工作流引擎转发
    ↓
节点完成，输出存入 context.results[node_id]
```

### 6.3 Chat @skill 执行流程

```
用户输入："@article-summary 这是一篇很长的文章..."
    ↓
parse_at_skill() → ("article-summary", "这是一篇很长的文章...")
    ↓
skill_loader.get_skill("article-summary")
    ↓
找到第一个 required input (article)，将消息内容作为其值
inputs = { "article": "这是一篇很长的文章..." }
    ↓
SkillExecutor.execute(skill, inputs)
    ↓
SSE 流式返回
```

## 7. 示例 Skill

### 7.1 文章摘要

```markdown
---
name: article-summary
description: 将长文章压缩成结构化要点。适用于新闻、论文、报告等长文本的快速提炼。
inputs:
  - name: article
    label: 文章内容
    type: textarea
    required: true
  - name: max_points
    label: 最大要点数
    type: text
    default: "5"
model:
  temperature: 0.3
  max_tokens: 1000
---

请将以下文章总结为不超过 {{max_points}} 个要点：

{{article}}

## 输出格式

- 每个要点一行，以 "•" 开头
- 保留关键数据和数字
- 标注信息来源（如有）
```

### 7.2 代码审查

```markdown
---
name: code-review
description: 审查代码质量，检查潜在问题和改进建议。支持多种编程语言。
inputs:
  - name: code
    label: 代码内容
    type: textarea
    required: true
  - name: language
    label: 编程语言
    type: text
    default: "auto"
  - name: focus
    label: 审查重点
    type: text
    default: "安全性、性能、可读性"
model:
  temperature: 0.2
  max_tokens: 2000
---

请审查以下 {{language}} 代码，重点关注 {{focus}}：

```
{{code}}
```

## 审查要求

1. 指出具体问题，说明原因和潜在风险
2. 给出改进建议和示例代码
3. 如果代码质量良好，也请指出优点
```

### 7.3 带知识库的 Skill

```markdown
---
name: product-qa
description: 基于产品知识库回答用户问题。
inputs:
  - name: question
    label: 用户问题
    type: text
    required: true
knowledge_base: product-docs
model:
  temperature: 0.5
  max_tokens: 1500
---

用户问题：{{question}}

请根据知识库中的产品文档回答以上问题。

## 回答要求

- 准确引用文档内容
- 如果知识库中没有相关信息，明确告知用户
- 提供相关文档链接（如有）
```

## 8. 开发顺序建议

### Phase 1: 基础 CRUD（P0）

1. `backend/app/models/skill.py` - 数据模型
2. `backend/app/core/skill_loader.py` - 文件解析
3. `backend/app/api/skill.py` - CRUD API
4. `backend/main.py` - 注册路由
5. 创建 `/skills/` 目录和示例 skill

### Phase 2: 前端列表和编辑（P0）

6. `frontend/src/views/SkillsView.vue` - 列表页
7. `frontend/src/views/SkillEditor.vue` - 编辑页
8. `frontend/src/router/index.ts` - 路由
9. `frontend/src/App.vue` - 导航

### Phase 3: 执行能力（P0）

10. `backend/app/core/skill_executor.py` - 执行逻辑
11. Skill 独立运行 API 和前端弹窗
12. 工作流 Skill 节点

### Phase 4: Chat 集成（P1）

13. Chat @skill 解析和执行
14. 输入框 @ 提示补全

### Phase 5: 高级功能（P2）

15. LLM 节点"从 Skill 加载"
16. AI 辅助创建 Skill 弹窗

## 9. 测试用例

### 9.1 API 测试

```python
# test_skill_api.py

def test_list_skills():
    """GET /api/v1/skills 返回 skill 列表"""
    pass

def test_get_skill():
    """GET /api/v1/skills/{name} 返回 skill 详情"""
    pass

def test_create_skill():
    """POST /api/v1/skills 创建新 skill"""
    pass

def test_create_skill_invalid_name():
    """name 不符合规范时返回 400"""
    pass

def test_run_skill():
    """POST /api/v1/skills/{name}/run 执行 skill"""
    pass

def test_run_skill_missing_required_input():
    """缺少必填 input 时返回 400"""
    pass
```

### 9.2 前端测试

```typescript
// SkillsView.spec.ts

it('显示 skill 列表')
it('点击卡片跳转到编辑页')
it('新建按钮跳转到新建页')

// SkillEditor.spec.ts

it('加载并显示 skill 内容')
it('保存修改')
it('运行测试')
```

## 10. 注意事项

1. **文件名校验**：name 必须是合法的文件夹名，不允许特殊字符
2. **并发安全**：多人同时编辑同一 skill 时使用 FileLock
3. **大文件处理**：限制 SKILL.md 大小（建议 < 50KB）
4. **错误处理**：解析失败时返回友好错误信息，不要暴露文件路径
5. **向后兼容**：扩展字段都是可选的，纯 Agent Skills 标准文件也能加载

## 11. 与用户管理系统集成



### 11.1 并行开发策略

Skill 系统与用户管理系统可以并行开发，集成点在 Wave 3 处理。

```
Wave 1（并行）:
├── 用户管理: Backend auth + SQLite models
└── Skill 系统: Backend CRUD + 前端列表编辑

Wave 2（并行）:
├── 用户管理: Frontend login + admin UI
└── Skill 系统: 执行能力 + 工作流节点

Wave 3（集成）:
└── Skill API 加 auth 保护 + user_id 从 token 获取
```

### 11.2 用户隔离设计

**Phase 1（无用户系统）：**
- `user_id` 字段保持 null
- 所有 skill 全局可见

**Phase 2（集成用户系统后）：**
- Skill API 添加 `get_current_user` 依赖
- 创建 skill 时自动填充 `user_id`
- 列表 API 可选参数 `?scope=mine|all`（admin 可查看全部）

### 11.3 API 权限矩阵

| API | 未登录 | 普通用户 | 管理员 |
|-----|--------|----------|--------|
| GET /skills | 401 | 自己的 + 公共的 | 全部 |
| GET /skills/{name} | 401 | 自己的 + 公共的 | 全部 |
| POST /skills | 401 | ✅ (user_id=self) | ✅ |
| PUT /skills/{name} | 401 | 仅自己的 | 全部 |
| DELETE /skills/{name} | 401 | 仅自己的 | 全部 |
| POST /skills/{name}/run | 401 | 自己的 + 公共的 | 全部 |

### 11.4 user_id 类型约定

为兼容用户管理系统的任何 ID 格式，Skill 的 `user_id` 使用 **string 类型**：

```python
# backend/app/models/skill.py
user_id: Optional[str] = None  # 存储用户 ID 的字符串形式
```

### 11.5 待集成任务清单

用户管理系统完成后，需要补充以下工作：

- [ ] `backend/app/api/skill.py` - 所有端点添加 `Depends(get_current_user)`
- [ ] `backend/app/api/skill.py` - 创建时自动设置 `user_id = current_user.id`
- [ ] `backend/app/api/skill.py` - 列表/详情/更新/删除添加权限检查
- [ ] `backend/app/core/skill_loader.py` - `list_skills()` 支持 `user_id` 过滤
- [ ] `frontend/src/views/SkillsView.vue` - 添加"我的/全部"切换（admin）
- [ ] SKILL.md frontmatter 写入时自动填充 `user_id`
