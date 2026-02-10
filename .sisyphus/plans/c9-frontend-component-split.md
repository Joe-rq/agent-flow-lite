# C9: 前端超长组件拆分计划（B+ -> A-）

> **状态**: 已完成（已逐项核对并标记）
> **目标**: 7 个超 500 行 Vue 组件全部拆至 ≤200 行，基线测试全绿
> **策略**: 6 个 Wave，逐步拆分，每 Wave 独立验证 + stop/go 门控

---

## 当前问题

| 组件 | 行数 | template | script | style |
|------|------|----------|--------|-------|
| ChatTerminal.vue | **~1156** | 164 | 518 | ~470 |
| KnowledgeView.vue | **1080** | 212 | 298 | 570 |
| WorkflowEditor.vue | **1012** | 224 | 490 | 300 |
| SkillsView.vue | 736 | 129 | 210 | 400 |
| SkillEditor.vue | 724 | 143 | 191 | 390 |
| NodeConfigPanel.vue | 634 | 156 | 238 | 240 |
| AdminUsersView.vue | 506 | 97 | 157 | 252 |

**核心发现**: style 块占每个组件 30-54% 的行数。提取 style 是低风险、高收益的第一步。

---

## Wave 0：基础设施（style 提取 + 共享 composable）

### 0A：提取 style 到独立 .css 文件

每个 `.vue` 的 `<style scoped>` 块提取为同目录 `.css` 文件，优先使用 `src` 形式以保持 scoped 语义：

```vue
<style scoped src="./KnowledgeView.css"></style>
```

**新建文件（7 个 .css）：**

| 文件 | 预估行数 |
|------|----------|
| `frontend/src/views/KnowledgeView.css` | ~570 |
| `frontend/src/views/WorkflowEditor.css` | ~300 |
| `frontend/src/views/ChatTerminal.css` | ~470 |
| `frontend/src/views/SkillsView.css` | ~400 |
| `frontend/src/views/SkillEditor.css` | ~390 |
| `frontend/src/views/AdminUsersView.css` | ~250 |
| `frontend/src/components/NodeConfigPanel.css` | ~240 |

**修改文件（7 个 .vue）：**
- `frontend/src/views/KnowledgeView.vue`
- `frontend/src/views/WorkflowEditor.vue`
- `frontend/src/views/ChatTerminal.vue`
- `frontend/src/views/SkillsView.vue`
- `frontend/src/views/SkillEditor.vue`
- `frontend/src/views/AdminUsersView.vue`
- `frontend/src/components/NodeConfigPanel.vue`

**效果**: 每个 .vue 文件立即减少 240-570 行。

**风险说明**: style 抽离后需确认 scoped 语义保持不变，存在以下边界情况需回归验证：
1. `:deep()` 选择器在 `scoped src` 外链样式中是否正常穿透
2. `v-bind()` CSS 动态绑定（如果存在）在 `scoped src` 外链样式中是否生效
3. CSS 变量引用和 `var()` 是否被 scoped 正确处理

### 0A Stop/Go 条件
- [x] `npx tsc --noEmit` 通过
- [x] `npm run test` 基线全绿
- [x] `npm run build` 成功
- [x] `npx vitest run src/__tests__/views/KnowledgeView.spec.ts src/__tests__/views/WorkflowEditor.spec.ts` 通过（覆盖 style 改动高相关页面）
- 任一失败 → 回滚该组件 style 提取，逐个排查

### 0B：创建共享 composable

**`frontend/src/composables/useSSEStream.ts`**（~60 行）
- 封装 `fetch` -> `ReadableStream` -> `createSSEParser` -> 事件回调的通用模式
- 被 ChatTerminal、SkillsView、WorkflowEditor 三个组件复用
- 复用已有的 `frontend/src/utils/sse-parser.ts`

### 0B Stop/Go 条件
- [x] `npx tsc --noEmit` 通过
- [x] 新增 composable 文件有正确的类型导出
- 此步仅新建文件，不修改现有组件，无回归风险

### Style 提取后各组件行数

| 组件 | 提取前 | 提取后 |
|------|--------|--------|
| KnowledgeView | 1080 | ~512 |
| WorkflowEditor | 1012 | ~718 |
| ChatTerminal | ~1156 | ~686 |
| SkillsView | 736 | ~343 |
| SkillEditor | 724 | ~337 |
| NodeConfigPanel | 634 | ~396 |
| AdminUsersView | 506 | ~258 |

---

## Wave 1：KnowledgeView（512 -> ~130 行）

### 新建文件

| 新文件 | 类型 | 预估行数 | 职责 |
|--------|------|----------|------|
| `frontend/src/composables/knowledge/useKnowledgeApi.ts` | composable | ~90 | 全部 API 调用 + 状态 + 轮询 |
| `frontend/src/components/knowledge/KbUploadArea.vue` | 组件 | ~60 | 上传拖拽区 |
| `frontend/src/components/knowledge/KbUploadArea.css` | 样式 | ~70 | |
| `frontend/src/components/knowledge/KbSearchTest.vue` | 组件 | ~70 | 检索测试区 |
| `frontend/src/components/knowledge/KbSearchTest.css` | 样式 | ~90 | |
| `frontend/src/components/knowledge/KbDocumentTable.vue` | 组件 | ~55 | 文档列表表格 |
| `frontend/src/components/knowledge/KbDocumentTable.css` | 样式 | ~80 | |

### 修改文件

`frontend/src/views/KnowledgeView.vue` 简化为 ~130 行（模板 ~55 + 脚本 ~70 + style-import ~5）

### 测试影响

`frontend/src/__tests__/views/KnowledgeView.spec.ts` 通过 `mount(KnowledgeView)` 测试，子组件在父组件内渲染，文本断言不受影响。不使用 `setupState`。

### Wave 1 Stop/Go 条件
- [x] `npx tsc --noEmit` 通过
- [x] `npm run test` 基线全绿（重点关注 `KnowledgeView.spec.ts` 套件）
- [x] `npm run build` 成功
- [x] `KnowledgeView.vue` 行数 ≤200

---

## Wave 2：WorkflowEditor（718 -> ~160 行）

### 新建文件

| 新文件 | 类型 | 预估行数 | 职责 |
|--------|------|----------|------|
| `frontend/src/composables/workflow/useWorkflowCrud.ts` | composable | ~85 | 保存/加载/删除工作流 |
| `frontend/src/composables/workflow/useWorkflowExecution.ts` | composable | ~75 | 执行工作流 + SSE |
| `frontend/src/composables/workflow/useNodeDragDrop.ts` | composable | ~65 | 拖拽添加节点 |
| `frontend/src/components/workflow/WorkflowRunDialog.vue` | 组件 | ~65 | 运行对话框 |
| `frontend/src/components/workflow/WorkflowRunDialog.css` | 样式 | ~60 | |
| `frontend/src/components/workflow/WorkflowLoadDialog.vue` | 组件 | ~45 | 加载对话框 |
| `frontend/src/components/workflow/WorkflowLoadDialog.css` | 样式 | ~50 | |
| `frontend/src/components/workflow/NodeDrawer.vue` | 组件 | ~75 | 节点抽屉面板 |
| `frontend/src/components/workflow/NodeDrawer.css` | 样式 | ~80 | |

### 修改文件

`frontend/src/views/WorkflowEditor.vue` 简化为 ~160 行（模板 ~60 + 脚本 ~95 + style-import ~5）

### 测试影响

`frontend/src/__tests__/views/WorkflowEditor.spec.ts` mock 了 VueFlow 和子组件，检查文本内容。不使用 `setupState`。子组件在父组件内渲染，断言不受影响。

### Wave 2 Stop/Go 条件
- [x] `npx tsc --noEmit` 通过
- [x] `npm run test` 基线全绿（重点关注 `WorkflowEditor.spec.ts` 套件）
- [x] `npm run build` 成功
- [x] `WorkflowEditor.vue` 行数 ≤200

---

## Wave 3：ChatTerminal（686 -> ~100 行）⚠️ 高风险

### 风险说明

`frontend/src/__tests__/views/ChatTerminal.spec.ts` 大量直接访问组件内部 `setupState`。composable 提取后必须在 setup 作用域解构暴露，保持测试兼容。

**必须保持可通过 `setupState` 访问的属性完整清单：**

| 属性名 | 来源 composable | 用途 |
|--------|----------------|------|
| `buildChatPayload` | useChatSSE | 构建聊天请求体 |
| `sessions` | useChatSession | 会话列表 |
| `currentSessionId` | useChatSession | 当前会话 ID |
| `activeCitation` | useChatSession | 当前引用源 |
| `handleSSEEvent` | useChatSSE | SSE 事件处理 |
| `currentThought` | useChatSSE | 当前思考状态 |
| `skills` | useSkillAutocomplete | 技能列表 |
| `inputMessage` | useSkillAutocomplete | 输入消息 |
| `onInputChange` | useSkillAutocomplete | 输入变化处理 |
| `showSuggestions` | useSkillAutocomplete | 是否显示建议 |
| `filteredSkills` | useSkillAutocomplete | 过滤后技能列表 |
| `selectSuggestion` | useSkillAutocomplete | 选择建议 |

### 新建文件

| 新文件 | 类型 | 预估行数 | 职责 |
|--------|------|----------|------|
| `frontend/src/composables/chat/useChatSession.ts` | composable | ~85 | 会话 CRUD + 状态 |
| `frontend/src/composables/chat/useChatSSE.ts` | composable | ~90 | SSE 流 + 事件处理 |
| `frontend/src/composables/useSkillAutocomplete.ts` | composable | ~55 | 技能 @ 补全 |
| `frontend/src/components/chat/ChatSidebar.vue` | 组件 | ~55 | 会话列表侧边栏 |
| `frontend/src/components/chat/ChatSidebar.css` | 样式 | ~90 | |
| `frontend/src/components/chat/ChatMessageList.vue` | 组件 | ~60 | 消息列表 + 引用 |
| `frontend/src/components/chat/ChatMessageList.css` | 样式 | ~150 | |
| `frontend/src/components/chat/ChatInputBar.vue` | 组件 | ~70 | 输入框 + 配置 + 补全 |
| `frontend/src/components/chat/ChatInputBar.css` | 样式 | ~100 | |

### 修改文件

`frontend/src/views/ChatTerminal.vue` 简化为 ~100 行

### 关键约束

composable 返回值必须在 setup 中解构（不能包装在嵌套对象中），使 `wrapper.vm.$.setupState.handleSSEEvent` 等仍可在测试中直接访问：

```typescript
// ChatTerminal.vue <script setup> 中
const { sessions, currentSessionId, activeCitation, ... } = useChatSession()
const { handleSSEEvent, buildChatPayload, currentThought, ... } = useChatSSE(...)
const { skills, inputMessage, onInputChange, showSuggestions, filteredSkills, selectSuggestion, ... } = useSkillAutocomplete()
```

### Wave 3 Stop/Go 条件（必须全部通过才可进入 Wave 4）
- [x] `npx tsc --noEmit` 通过
- [x] `npm run test` 基线全绿
- [x] **关键套件**: `ChatTerminal.spec.ts` 全部 case 通过，特别是：
  - `buildChatPayload` 测试（行 81-90）
  - `handleSSEEvent` 全系列测试（行 147-225）
  - `onInputChange / selectSuggestion` 自动补全测试（行 243-282）
- [x] 上述 12 个 setupState 属性均可通过 `wrapper.vm.$.setupState.xxx` 访问
- [x] `npm run build` 成功
- [x] `ChatTerminal.vue` 行数 ≤200

---

## Wave 4：SkillsView + SkillEditor（343 + 337 -> ~155 + ~160 行）

### SkillsView 新建文件

| 新文件 | 类型 | 预估行数 | 职责 |
|--------|------|----------|------|
| `frontend/src/composables/skills/useSkillRunner.ts` | composable | ~80 | 运行技能 + SSE |
| `frontend/src/components/skills/SkillRunDialog.vue` | 组件 | ~70 | 运行对话框 UI |
| `frontend/src/components/skills/SkillRunDialog.css` | 样式 | ~140 | |

### SkillEditor 新建文件

| 新文件 | 类型 | 预估行数 | 职责 |
|--------|------|----------|------|
| `frontend/src/composables/skills/useSkillForm.ts` | composable | ~85 | 编辑验证 + Markdown 生成 |
| `frontend/src/components/skills/SkillPreviewPane.vue` | 组件 | ~50 | 预览面板 |
| `frontend/src/components/skills/SkillPreviewPane.css` | 样式 | ~80 | |

### 修改文件

- `frontend/src/views/SkillsView.vue`
- `frontend/src/views/SkillEditor.vue`

### 测试影响

`frontend/src/__tests__/views/SkillsView.spec.ts` 和 `frontend/src/__tests__/views/SkillEditor.spec.ts` 均不使用 `setupState`，通过 `mount` 测试文本内容。
`frontend/src/__tests__/skills/sse-handler.spec.ts` 测试 SSE 解析工具函数，与组件拆分无关。

### Wave 4 Stop/Go 条件
- [x] `npx tsc --noEmit` 通过
- [x] `npm run test` 基线全绿（重点关注 `SkillsView.spec.ts`、`SkillEditor.spec.ts`、`sse-handler.spec.ts`）
- [x] `npm run build` 成功
- [x] `SkillsView.vue` 和 `SkillEditor.vue` 行数均 ≤200

---

## Wave 5：NodeConfigPanel + AdminUsersView（396 + 258 -> ~110 + ~130 行）

### NodeConfigPanel 新建文件

| 新文件 | 类型 | 预估行数 | 职责 |
|--------|------|----------|------|
| `frontend/src/composables/workflow/useNodeConfig.ts` | composable | ~70 | 配置加载/保存 |
| `frontend/src/components/config/LlmNodeConfig.vue` | 组件 | ~55 | LLM 节点配置 |
| `frontend/src/components/config/SkillNodeConfig.vue` | 组件 | ~55 | Skill 节点配置 |

### AdminUsersView 新建文件

| 新文件 | 类型 | 预估行数 | 职责 |
|--------|------|----------|------|
| `frontend/src/composables/useUserAdmin.ts` | composable | ~70 | 用户管理 API + 状态 |

### 修改文件

- `frontend/src/components/NodeConfigPanel.vue`
- `frontend/src/views/AdminUsersView.vue`

### 测试影响

`frontend/src/__tests__/admin/users.spec.ts` 不使用 `setupState`。

### Wave 5 Stop/Go 条件
- [x] `npx tsc --noEmit` 通过
- [x] `npm run test` 基线全绿（重点关注 `users.spec.ts`）
- [x] `npm run build` 成功
- [x] `NodeConfigPanel.vue` 和 `AdminUsersView.vue` 行数均 ≤200

---

## 最终目录结构

```
frontend/src/
├── composables/                    (4 文件 + 4 子目录)
│   ├── useSSEStream.ts
│   ├── useSkillAutocomplete.ts
│   ├── useUserAdmin.ts
│   ├── knowledge/
│   │   └── useKnowledgeApi.ts
│   ├── workflow/
│   │   ├── useWorkflowCrud.ts
│   │   ├── useWorkflowExecution.ts
│   │   ├── useNodeDragDrop.ts
│   │   └── useNodeConfig.ts
│   ├── chat/
│   │   ├── useChatSession.ts
│   │   └── useChatSSE.ts
│   └── skills/
│       ├── useSkillRunner.ts
│       └── useSkillForm.ts
├── components/
│   ├── nodes/                      (不变)
│   ├── ui/                         (不变)
│   ├── NodeConfigPanel.vue         (~110 行)
│   ├── NodeConfigPanel.css
│   ├── knowledge/                  (6 文件: 3 vue + 3 css)
│   ├── workflow/                   (6 文件: 3 vue + 3 css)
│   ├── chat/                       (6 文件: 3 vue + 3 css)
│   ├── skills/                     (4 文件: 2 vue + 2 css)
│   └── config/                     (2 文件: 2 vue)
├── views/
│   ├── KnowledgeView.vue           (~130 行)
│   ├── KnowledgeView.css
│   ├── WorkflowEditor.vue          (~160 行)
│   ├── WorkflowEditor.css
│   ├── ChatTerminal.vue            (~100 行)
│   ├── ChatTerminal.css
│   ├── SkillsView.vue              (~155 行)
│   ├── SkillsView.css
│   ├── SkillEditor.vue             (~160 行)
│   ├── SkillEditor.css
│   ├── AdminUsersView.vue          (~130 行)
│   ├── AdminUsersView.css
│   └── ... (HomeView, LoginView 不变)
└── ... (stores/, router/, utils/, types/ 不变)
```

---

## 新建文件汇总

| Wave | 新建文件数 | 文件列表 |
|------|-----------|----------|
| 0A | 7 | 7 个 .css |
| 0B | 1 | `frontend/src/composables/useSSEStream.ts` |
| 1 | 7 | 1 composable + 3 vue + 3 css |
| 2 | 9 | 3 composable + 3 vue + 3 css |
| 3 | 9 | 3 composable + 3 vue + 3 css |
| 4 | 6 | 2 composable + 2 vue + 2 css |
| 5 | 4 | 2 composable + 2 vue |
| **总计** | **43** | |

## 修改文件汇总

| Wave | 修改文件（全路径） |
|------|----------|
| 0A | `frontend/src/views/{KnowledgeView,WorkflowEditor,ChatTerminal,SkillsView,SkillEditor,AdminUsersView}.vue`, `frontend/src/components/NodeConfigPanel.vue` |
| 0B | 无（仅新建） |
| 1 | `frontend/src/views/KnowledgeView.vue` |
| 2 | `frontend/src/views/WorkflowEditor.vue` |
| 3 | `frontend/src/views/ChatTerminal.vue` |
| 4 | `frontend/src/views/SkillsView.vue`, `frontend/src/views/SkillEditor.vue` |
| 5 | `frontend/src/components/NodeConfigPanel.vue`, `frontend/src/views/AdminUsersView.vue` |

---

## 验证步骤（每个 Wave 完成后）

```bash
cd frontend
npx tsc --noEmit              # 类型检查必须通过
npm run test                  # 基线测试全绿（当前基线全部通过即可，不绑定具体数字）
npm run build                 # 构建必须成功
```

### 关键测试套件（按 Wave 重点关注）

| Wave | 关键测试套件 |
|------|-------------|
| 0A | 全部套件（style 回归） |
| 1 | `KnowledgeView.spec.ts` |
| 2 | `WorkflowEditor.spec.ts` |
| 3 | `ChatTerminal.spec.ts`（setupState 兼容性最高优先级） |
| 4 | `SkillsView.spec.ts`, `SkillEditor.spec.ts`, `sse-handler.spec.ts` |
| 5 | `users.spec.ts` |

### 执行方式约束（资源安全）

- `type-check`、`test`、`build` 必须串行执行，禁止并行
- 仅使用一次性测试命令（`npm run test` 或 `npx vitest run`），禁止 watch 模式
- 保持 `frontend/vitest.config.ts` 中 worker 限制（`maxForks: 2`）不变

---

## 预期结果

| 指标 | 当前 | 完成后 |
|------|------|--------|
| 超过 500 行的 Vue 文件 | 7 个 | **0 个** |
| 超过 200 行的 Vue 文件 | 9 个 | **≤2 个** |
| 前端测试 | 基线全绿 | **基线全绿** |
| 类型检查 | 通过 | **通过** |
| 评级 | B+ | **A-** |

---

## 执行规则

1. **每个 Wave 独立提交**，便于回滚
2. **Wave 0 先做**，这是低风险操作，且后续 Wave 都依赖它
3. **Wave 3（ChatTerminal）风险最高**，因为测试直接访问 setupState，需格外谨慎
4. **不改变任何 CSS 类名**，测试依赖选择器匹配
5. **不改变任何 API 调用路径或用户可见行为**
6. **不改变任何组件的 props/emits 接口**
7. **每个 Wave 的 Stop/Go 条件必须全部满足才可进入下一 Wave**
8. **任何 Wave 失败时**，回滚该 Wave 全部改动，排查问题后重试
