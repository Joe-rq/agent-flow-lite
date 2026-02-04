# Frontend - Vue 3 前端应用

Agent Flow Lite 的 Vue 3 前端应用，提供可视化工作流编辑、知识库管理和智能对话界面。

## 🏗️ 技术架构

### 核心框架
- **Vue 3** - 渐进式 JavaScript 框架（Composition API）
- **Vite** - 下一代前端构建工具
- **TypeScript** - 类型安全的 JavaScript 超集

### UI 组件与状态
- **Vue Flow** - 可视化工作流画布
- **Pinia** - Vue 3 状态管理
- **Element Plus** - UI 组件库

### 开发工具
- **Vitest** - 单元测试框架
- **ESLint + OXLint** - 代码检查
- **Prettier** - 代码格式化

## 📁 项目结构

```
frontend/
├── src/
│   ├── assets/           # 静态资源
│   ├── components/       # 组件
│   │   ├── nodes/      # 工作流节点组件
│   │   │   ├── StartNode.vue
│   │   │   ├── LLMNode.vue
│   │   │   ├── KnowledgeNode.vue
│   │   │   ├── ConditionNode.vue
│   │   │   └── EndNode.vue
│   │   ├── ui/         # 通用 UI 组件
│   │   │   ├── Button.vue
│   │   │   ├── Card.vue
│   │   │   ├── Modal.vue
│   │   │   └── Input.vue
│   │   ├── NodeConfigPanel.vue  # 节点配置面板
│   │   └── NodeDrawer.vue       # 节点抽屉
│   ├── styles/           # 全局样式
│   │   ├── theme.css           # 主题变量
│   │   └── animations.css     # 动画定义
│   ├── stores/           # Pinia 状态
│   │   ├── workflow.ts         # 工作流状态
│   │   └── chat.ts            # 聊天状态
│   ├── views/            # 页面视图
│   │   ├── HomeView.vue        # 首页
│   │   ├── WorkflowView.vue    # 工作流管理
│   │   ├── WorkflowEditor.vue  # 工作流编辑器
│   │   ├── KnowledgeView.vue   # 知识库管理
│   │   └── ChatTerminal.vue   # 智能对话
│   ├── App.vue          # 根组件
│   └── main.ts          # 应用入口
├── public/             # 公共资源
├── index.html           # HTML 模板
├── vite.config.ts       # Vite 配置
├── tsconfig.json        # TypeScript 配置
├── eslint.config.ts     # ESLint 配置
└── package.json        # 依赖配置
```

## 🚀 快速开始

### 1. 环境准备

确保已安装 Node.js ^20.19.0 或 >=22.12.0。

```bash
node --version  # 检查版本
```

### 2. 安装依赖

```bash
npm install
```

### 3. 启动开发服务器

```bash
npm run dev
```

应用将在 http://localhost:5173 启动。

### 4. 访问应用

| 页面 | 路径 |
|------|------|
| 首页 | `/` |
| 工作流 | `/workflow` |
| 知识库 | `/knowledge` |
| 对话 | `/chat` |

## 🛠️ 开发命令

```bash
# 开发服务器（热重载）
npm run dev

# 生产构建（类型检查 + 打包）
npm run build

# 仅构建（不检查类型）
npm run build-only

# 预览生产构建
npm run preview

# 类型检查
npm run type-check

# 代码检查（ESLint + OXLint）
npm run lint

# 仅 ESLint
npm run lint:eslint

# 仅 OXLint
npm run lint:oxlint

# 代码格式化
npm run format

# 运行所有测试
npm run test

# 运行测试（UI 模式）
npm run test:ui
```

## 🧪 测试

### 运行所有测试

```bash
npm run test
```

### 运行单个测试文件

```bash
npx vitest run src/__tests__/views/ChatTerminal.spec.ts
```

### Watch 模式（自动重新运行）

```bash
npx vitest src/__tests__/views/ChatTerminal.spec.ts
```

### 测试覆盖率

```bash
npx vitest run --coverage
```

## 📝 组件说明

### 工作流编辑器 (WorkflowEditor.vue)

可视化工作流编排的核心组件。

**功能：**
- 顶部工具栏：保存、加载、运行、删除、自动布局
- 左侧信息面板：显示工作流元数据
- 右侧抽屉：节点添加入口
- 主画布：拖拽节点、连接边、配置节点

**技术：**
- Vue Flow（@vue-flow/core）
- SSE 流式事件处理
- 节点数据双向绑定

### 智能对话 (ChatTerminal.vue)

多轮对话终端，支持流式响应和引用溯源。

**功能：**
- SSE 流式消息显示
- 知识库/工作流选择
- 引用按钮和详情面板
- 会话历史管理

**技术：**
- EventSource 处理 SSE
- Pinia 状态管理
- Axios HTTP 客户端

### 知识库管理 (KnowledgeView.vue)

文档上传和知识库管理界面。

**功能：**
- 创建知识库
- 文件拖拽上传
- 向量化进度显示
- 文档列表管理

**技术：**
- FormData 文件上传
- 轮询任务状态

##### 样式系统

### 主题变量 (theme.css)

定义全局 CSS 变量，支持深色主题。

**主要变量：**
```css
--bg-primary: #0d1117      /* 主背景色 */
--bg-secondary: #161b22     /* 次背景色 */
--bg-tertiary: #21262d     /* 三级背景色 */
--accent-cyan: #00d4ff      /* 青色强调 */
--accent-purple: #a855f7     /* 紫色强调 */
--text-primary: #e6edf3      /* 主文字色 */
--text-secondary: #8b949e     /* 次文字色 */
--border-primary: #30363d     /* 边框色 */
```

### 动画 (animations.css)

全局动画定义。

**可用动画：**
- `animate-fade-in` - 淡入
- `animate-slide-up` - 向上滑动
- `animate-pulse` - 脉冲
- `animate-glow` - 发光效果

## 🔧 推荐开发设置

### IDE 设置

**Visual Studio Code:**

1. 安装 [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar)
2. 禁用 Vetur（如果有）
3. 安装 [ESLint](https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint)
4. 安装 [Prettier](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)

**浏览器设置:**

**Chrome / Edge / Brave:**
- [Vue.js devtools](https://chromewebstore.google.com/detail/vuejs-devtools/nhdogjmejiglipccpnnnanhbledajbpd)
- 启用 Custom Object Formatter

**Firefox:**
- [Vue.js devtools](https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/)
- 启用 Custom Object Formatter

## 🐛 常见问题

<details>
<summary>开发服务器启动失败</summary>

**症状**: `npm run dev` 报错

**排查**:
1. 检查 Node.js 版本是否符合要求
2. 删除 `node_modules` 和 `package-lock.json`，重新 `npm install`
3. 检查端口 5173 是否被占用
</details>

<details>
<summary>类型检查错误</summary>

**症状**: `npm run type-check` 报错

**解决**:
1. 检查 TypeScript 版本是否兼容
2. 确保 `tsconfig.json` 配置正确
3. 检查导入路径是否正确
</details>

<details>
<summary>代理连接失败</summary>

**症状**: 无法连接后端 API

**解决**:
1. 检查 `vite.config.ts` 中的 proxy 配置
2. 确保后端服务运行在 8000 端口
3. 检查 CORS 配置
</details>

<details>
<summary>SSE 流式响应不工作</summary>

**症状**: 前端收不到流式数据

**解决**:
1. 检查后端 SSE 接口是否正常
2. 检查浏览器控制台是否有错误
3. 确认 EventSource 连接成功
</details>

## 📚 相关资源

- [Vue 3 官方文档](https://vuejs.org/)
- [Vite 文档](https://vite.dev/)
- [Vue Flow 文档](https://vueflow.dev/)
- [Pinia 文档](https://pinia.vuejs.org/)
- [Element Plus 文档](https://element-plus.org.cn/)
- [TypeScript 文档](https://www.typescriptlang.org/)
- [Vitest 文档](https://vitest.dev/)
