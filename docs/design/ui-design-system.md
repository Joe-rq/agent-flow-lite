# Agent Flow Lite UI 设计规范 v1.0

> 浅色科技风设计系统 - 让界面从"政务后台"升级为"现代 AI SaaS"

---

## 📋 目录

1. [设计概览](#设计概览)
2. [配色系统](#配色系统)
3. [组件规范](#组件规范)
4. [布局原则](#布局原则)
5. [动效系统](#动效系统)
6. [实施优先级](#实施优先级)
7. [参考风格](#参考风格)

---

## 🎯 设计概览

### 设计策略

浅色做科技感的难点在于**容易看起来像普通后台**。破解方法：

- ✅ 用**极淡的灰蓝调**替代纯白（减少刺眼感）
- ✅ 用**微妙的发光**替代强烈的阴影（营造通透感）
- ✅ 用**渐变色彩**替代单一色块（增加层次感）
- ✅ 用**大圆角**替代小圆角（更 modern）

### 设计关键词

```
云端 · 通透 · 轻盈 · 科技感 · 专业
```

### 与当前设计的对比

| 维度 | 当前设计 | 新设计 |
|------|---------|--------|
| 主色 | `#0891b2` (暗青色) | `#0ea5e9` (亮科技蓝) |
| 背景 | 纯白 `#ffffff` | 极淡灰 `#fafbfc` |
| 卡片 | 1px 实线边框 | 多层柔和阴影 + 细边框 |
| 圆角 | 8px | 16px |
| 按钮 | 单色填充 | 渐变 + 光晕 |
| 节点 | 彩色填充 | 白底 + 顶部彩条 |

---

## 🎨 配色系统

### CSS 变量定义

```css
:root {
  /* ========== 背景层次 ========== */
  --color-background: #fafbfc;           /* 主背景 - 极淡灰 */
  --color-background-elevated: #ffffff;   /* 卡片 - 纯白 */
  --color-background-surface: #f4f6f8;    /* 次级表面 */

  /* ========== 强调色 ========== */
  /* 主色：电光青蓝 - 更亮更有科技味 */
  --color-primary: #0ea5e9;              /* sky-500 */
  --color-primary-soft: rgba(14, 165, 233, 0.08);
  --color-primary-glow: rgba(14, 165, 233, 0.25);
  
  /* 次色：薰衣草紫 */
  --color-accent: #6366f1;               /* indigo-500 */
  --color-accent-soft: rgba(99, 102, 241, 0.08);
  --color-accent-glow: rgba(99, 102, 241, 0.25);

  /* ========== 边框 ========== */
  --color-border: rgba(148, 163, 184, 0.15);      /* 极淡 */
  --color-border-strong: rgba(148, 163, 184, 0.3); /* 稍强 */
  --color-border-focus: rgba(14, 165, 233, 0.4);   /* 聚焦时 */

  /* ========== 文字层级 ========== */
  --color-foreground: #0f172a;           /* slate-900 - 标题 */
  --color-foreground-muted: #64748b;     /* slate-500 - 正文 */
  --color-foreground-subtle: #94a3b8;    /* slate-400 - 提示 */

  /* ========== 功能色（克制使用）========== */
  --color-success: #10b981;              /* emerald-500 */
  --color-success-soft: rgba(16, 185, 129, 0.08);
  
  --color-warning: #f59e0b;              /* amber-500 */
  --color-warning-soft: rgba(245, 158, 11, 0.08);
  
  --color-destructive: #ef4444;          /* red-500 */
  --color-destructive-soft: rgba(239, 68, 68, 0.08);

  /* ========== 渐变定义 ========== */
  --gradient-primary: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
  --gradient-accent: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  --gradient-text: linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%);
}
```

### 配色使用原则

```
背景层次：
  页面背景 → --color-background (#fafbfc)
  卡片背景 → --color-background-elevated (#ffffff)
  输入框/小区域 → --color-background-surface (#f4f6f8)

强调色使用：
  主按钮、选中状态、主要链接 → --color-primary (sky-500)
  次要操作、标签、徽章 → --color-accent (indigo-500)
  成功提示 → --color-success ( sparingly )
  警告提示 → --color-warning ( sparingly )
  危险操作 → --color-destructive ( sparingly )

文字层级：
  页面标题 → --color-foreground (slate-900), font-weight: 700
  卡片标题 → --color-foreground (slate-900), font-weight: 600
  正文内容 → --color-foreground-muted (slate-500)
  辅助说明 → --color-foreground-subtle (slate-400)
```

---

## 🧩 组件规范

### 1. 卡片组件 (Card)

#### 基础卡片

```css
.card {
  background: var(--color-background-elevated);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 24px;
  
  /* 多层柔和阴影营造悬浮感 */
  box-shadow: 
    0 1px 3px rgba(0, 0, 0, 0.02),      /* 底层：极浅 */
    0 4px 12px rgba(0, 0, 0, 0.04),     /* 中层：悬浮感 */
    inset 0 1px 0 rgba(255, 255, 255, 0.8); /* 顶部内发光 */
  
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.card:hover {
  transform: translateY(-3px);
  box-shadow: 
    0 12px 24px rgba(0, 0, 0, 0.06),    /* 增强悬浮感 */
    0 0 0 1px rgba(14, 165, 233, 0.15), /* 青色边框光晕 */
    0 0 20px rgba(14, 165, 233, 0.08);  /* 青色光晕 */
}
```

#### 统计卡片 (Stat Card)

```css
.stat-card {
  background: linear-gradient(135deg, #ffffff 0%, #fafbfc 100%);
  border: 1px solid var(--color-border);
  border-radius: 20px;
  padding: 32px 24px;
  text-align: center;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.06);
  border-color: rgba(14, 165, 233, 0.2);
}

.stat-number {
  font-size: 42px;
  font-weight: 700;
  background: var(--gradient-text);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: var(--color-foreground-muted);
  font-weight: 500;
}

.stat-action {
  margin-top: 16px;
  font-size: 13px;
  color: var(--color-primary);
  cursor: pointer;
}
```

---

### 2. 按钮组件 (Button)

#### 主按钮 (Primary Button)

```css
.btn-primary {
  background: var(--gradient-primary);
  color: white;
  border: none;
  border-radius: 12px;
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  
  box-shadow: 
    0 4px 12px rgba(14, 165, 233, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  
  transition: all 0.2s;
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 
    0 6px 20px rgba(14, 165, 233, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.btn-primary:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.25);
}
```

#### 次按钮 (Secondary Button)

```css
.btn-secondary {
  background: rgba(255, 255, 255, 0.8);
  color: #475569;
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 12px;
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  backdrop-filter: blur(8px);
  transition: all 0.2s;
}

.btn-secondary:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: rgba(14, 165, 233, 0.05);
  box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.1);
}
```

#### 文字按钮 (Text Button)

```css
.btn-text {
  background: transparent;
  color: var(--color-primary);
  border: none;
  padding: 8px 12px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-text:hover {
  background: rgba(14, 165, 233, 0.08);
  border-radius: 8px;
}
```

---

### 3. 工作流节点 (Workflow Nodes)

#### 节点基础样式

```css
.node {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 14px;
  min-width: 160px;
  padding: 16px;
  
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 1);
  
  transition: all 0.3s;
}

.node:hover {
  transform: scale(1.02);
}

.node.selected {
  box-shadow: 
    0 0 0 2px var(--color-primary),
    0 0 20px rgba(14, 165, 233, 0.3);
}

/* 节点头部 */
.node-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.node-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  font-size: 14px;
}

.node-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-foreground);
}

.node-description {
  font-size: 12px;
  color: var(--color-foreground-muted);
  line-height: 1.4;
}
```

#### 各类型节点配色

```css
/* Start Node - 启动：翠绿 */
.node-start {
  border-top: 3px solid #10b981;
  box-shadow: 
    0 4px 16px rgba(16, 185, 129, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 1);
}
.node-start .node-icon {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

/* LLM Node - 智能核心：科技蓝 */
.node-llm {
  border-top: 3px solid #0ea5e9;
  box-shadow: 
    0 4px 16px rgba(14, 165, 233, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 1);
}
.node-llm .node-icon {
  background: rgba(14, 165, 233, 0.1);
  color: #0ea5e9;
}

/* Knowledge Node - 知识：琥珀金 */
.node-knowledge {
  border-top: 3px solid #f59e0b;
  box-shadow: 
    0 4px 16px rgba(245, 158, 11, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 1);
}
.node-knowledge .node-icon {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

/* Skill Node - 技能：靛蓝 */
.node-skill {
  border-top: 3px solid #6366f1;
  box-shadow: 
    0 4px 16px rgba(99, 102, 241, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 1);
}
.node-skill .node-icon {
  background: rgba(99, 102, 241, 0.1);
  color: #6366f1;
}

/* Condition Node - 分支：洋红 */
.node-condition {
  border-top: 3px solid #ec4899;
  box-shadow: 
    0 4px 16px rgba(236, 72, 153, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 1);
}
.node-condition .node-icon {
  background: rgba(236, 72, 153, 0.1);
  color: #ec4899;
}

/* End Node - 结束：赤红 */
.node-end {
  border-top: 3px solid #ef4444;
  box-shadow: 
    0 4px 16px rgba(239, 68, 68, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 1);
}
.node-end .node-icon {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}
```

**节点设计要点**：
- 白底 + 顶部彩条（3px）代替全彩色填充
- 阴影使用对应类型的颜色（透明度 15%）
- 图标使用对应颜色的 10% 透明度背景
- 选中时外圈加科技蓝光晕

---

### 4. 侧边栏 (Sidebar)

```css
.sidebar {
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border-right: 1px solid var(--color-border);
  width: 260px;
  height: 100vh;
  padding: 16px 0;
}

.sidebar-header {
  padding: 0 20px 20px;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: 16px;
}

.sidebar-logo {
  font-size: 20px;
  font-weight: 700;
  background: var(--gradient-text);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* 导航项 */
.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  margin: 4px 12px;
  border-radius: 12px;
  color: var(--color-foreground-muted);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-item:hover {
  background: rgba(14, 165, 233, 0.06);
  color: var(--color-foreground);
}

.nav-item.active {
  background: linear-gradient(90deg, rgba(14, 165, 233, 0.1) 0%, rgba(99, 102, 241, 0.05) 100%);
  color: var(--color-primary);
  font-weight: 600;
  box-shadow: 
    inset 3px 0 0 var(--color-primary),
    0 2px 8px rgba(14, 165, 233, 0.1);
}

.nav-item.active .nav-icon {
  color: var(--color-primary);
}

.nav-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}
```

---

### 5. 输入框 (Input)

```css
.input {
  background: var(--color-background-surface);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 14px;
  color: var(--color-foreground);
  width: 100%;
  transition: all 0.2s;
}

.input::placeholder {
  color: var(--color-foreground-subtle);
}

.input:hover {
  border-color: var(--color-border-strong);
}

.input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.1);
  background: var(--color-background-elevated);
}
```

---

### 6. 标签/徽章 (Badge)

```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.badge-primary {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.badge-success {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.badge-warning {
  background: var(--color-warning-soft);
  color: var(--color-warning);
}

.badge-destructive {
  background: var(--color-destructive-soft);
  color: var(--color-destructive);
}
```

---

## 📐 布局原则

### 首页 Dashboard 布局

```
┌─────────────────────────────────────────────────────────┐
│  Agent Flow                                    [头像]   │  ← Header (64px)
├─────────────────────────────────────────────────────────┤
│  [侧边栏] │                                             │
│  260px   │  ┌─────────────────────────────────────┐   │
│          │  │ 👋 欢迎横幅                          │   │  ← 渐变背景卡片
│          │  │ 今日概览文字...                      │   │
│          │  └─────────────────────────────────────┘   │
│          │                                              │
│          │  ┌────────────┐ ┌────────────┐ ┌──────────┐ │  ← 统计卡片 (3列)
│          │  │   工作流   │ │   知识库   │ │   对话   │ │
│          │  │     12     │ │     5      │ │    28    │ │
│          │  │  ⚡ 运行    │ │  📄 管理   │ │  💬 查看 │ │
│          │  └────────────┘ └────────────┘ └──────────┘ │
│          │                                              │
│          │  ┌─────────────────────────────────────────┐ │  ← 最近动态
│          │  │ 📊 最近动态                              │ │
│          │  │ ● 14:32  运行了"文章总结工作流"   ✓ 成功 │ │
│          │  │ ● 11:15  上传了"产品文档.pdf"          │ │
│          │  │ ● 09:20  创建了"客服问答 Skill"        │ │
│          │  └─────────────────────────────────────────┘ │
│          │                                              │
│          │  ┌─────────────────────────────────────────┐ │  ← 快捷操作区
│          │  │ ⚡ 快捷操作     [+ 创建工作流] [+ 上传] │ │
│          │  └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 页面布局规范

```css
/* 页面容器 */
.page-container {
  display: flex;
  min-height: 100vh;
  background: var(--color-background);
}

/* 主内容区 */
.main-content {
  flex: 1;
  padding: 32px 40px;
  overflow-y: auto;
}

/* 页面标题 */
.page-header {
  margin-bottom: 32px;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-foreground);
  margin-bottom: 8px;
}

.page-subtitle {
  font-size: 15px;
  color: var(--color-foreground-muted);
}

/* 卡片网格 */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
  margin-top: 24px;
}

/* 统计卡片容器 */
.stats-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin: 24px 0;
}
```

---

## ✨ 动效系统

### 过渡时间函数

```css
:root {
  --ease-out: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  
  --duration-fast: 150ms;
  --duration-normal: 200ms;
  --duration-slow: 300ms;
}
```

### 关键帧动画

```css
/* 脉冲发光 - 用于选中状态 */
@keyframes pulse-glow {
  0%, 100% {
    box-shadow: 0 0 0 2px var(--color-primary), 0 0 20px rgba(14, 165, 233, 0.3);
  }
  50% {
    box-shadow: 0 0 0 2px var(--color-primary), 0 0 30px rgba(14, 165, 233, 0.5);
  }
}

.animate-pulse-glow {
  animation: pulse-glow 2s ease-in-out infinite;
}

/* 淡入上移动画 - 用于列表项 */
@keyframes fade-in-up {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in-up {
  animation: fade-in-up 0.5s var(--ease-out) forwards;
}

/* 数据流动画 - 用于工作流连线 */
@keyframes data-flow {
  0% {
    stroke-dashoffset: 20;
  }
  100% {
    stroke-dashoffset: 0;
  }
}

.animate-data-flow {
  animation: data-flow 1s linear infinite;
}

/* 轻微弹跳 - 用于按钮点击 */
@keyframes scale-bounce {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(0.95);
  }
}

.btn:active {
  animation: scale-bounce 0.2s var(--ease-spring);
}
```

### 悬停动效规范

```css
/* 卡片悬停 */
.card {
  transition: transform var(--duration-slow) var(--ease-out),
              box-shadow var(--duration-slow) var(--ease-out);
}

.card:hover {
  transform: translateY(-3px);
}

/* 按钮悬停 */
.btn {
  transition: all var(--duration-normal) var(--ease-out);
}

/* 导航项悬停 */
.nav-item {
  transition: background-color var(--duration-fast) var(--ease-out),
              color var(--duration-fast) var(--ease-out);
}

/* 输入框聚焦 */
.input {
  transition: border-color var(--duration-fast) var(--ease-out),
              box-shadow var(--duration-fast) var(--ease-out),
              background-color var(--duration-fast) var(--ease-out);
}
```

---

## 📋 实施优先级

### P0 - 立即实施（最大视觉 impact）

```
1. 更新配色系统 (app.css)
   - 修改 CSS 变量
   - 主色改为 sky-500 (#0ea5e9)
   - 背景改为极淡灰 (#fafbfc)
   预计时间: 30分钟

2. 重构按钮组件 (Button.vue)
   - 添加渐变背景
   - 添加光晕阴影
   预计时间: 1小时

3. 升级卡片样式 (各 View.vue 中的 card 类)
   - 圆角改为 16px
   - 添加多层阴影
   - 添加悬停动效
   预计时间: 2小时
```

### P1 - 显著提升（本周完成）

```
4. 重新设计工作流节点 (nodes/*.vue)
   - 改为白底 + 顶部彩条
   - 调整节点配色
   预计时间: 3小时

5. 重构首页 Dashboard (HomeView.vue)
   - 添加统计卡片
   - 添加最近动态列表
   - 添加欢迎横幅
   预计时间: 4小时

6. 优化侧边栏样式
   - 添加渐变背景
   - 优化选中态样式
   预计时间: 1.5小时
```

### P2 - 锦上添花（后续迭代）

```
7. 添加动效系统 (animations.css)
   - 入场动画
   - 选中脉冲动画
   - 页面切换动画
   预计时间: 3小时

8. 优化知识库列表页
   - 卡片重新设计
   - 添加操作按钮组
   预计时间: 2小时

9. 细节打磨
   - 图标统一
   - 间距微调
   - 响应式适配
   预计时间: 4小时
```

---

## 🎨 参考风格

### 推荐参考产品

1. **Notion** (notion.so)
   - 极淡灰背景 (#f7f6f3)
   - 微妙阴影
   - 紫色强调色

2. **Linear** (linear.app)
   - 纯白卡片
   - 极细边框
   - 青色点缀
   - 精致动效

3. **Figma** (figma.com)
   - 紫色强调色
   - 柔和阴影
   - 大圆角设计

4. **Raycast Store** (raycast.com/store)
   - 浅色玻璃拟态
   - 精致图标
   - 渐变运用

5. **Vercel Dashboard** (vercel.com/dashboard)
   - 统计卡片设计
   - 数据可视化风格
   - 现代排版

---

## 📝 最小改动方案

如果你只想最小改动提升质感，**只做这3件事**：

```css
/* 1. 改主色 */
--color-primary: #0ea5e9;  /* sky-500，更亮的科技蓝 */

/* 2. 加卡片悬浮感 */
.card {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
  border-radius: 16px;
  transition: all 0.3s;
}
.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
}

/* 3. 按钮加渐变 */
.btn-primary {
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.25);
}
```

**这3行 CSS 就能让你的界面从「政府网站」变成「现代 SaaS」。**

---

## 🔄 版本历史

- **v1.0** (2026-02-21) - 初始版本，浅色科技风设计系统

---

> 💡 **提示**：本文档为设计规范，具体实现时请根据实际组件结构进行适配。
> 建议在 `frontend/src/assets/` 目录下新建 `design-system.css` 存放这些变量和基础样式。
