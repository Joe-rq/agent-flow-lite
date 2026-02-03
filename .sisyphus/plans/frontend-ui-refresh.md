# 前端UI/UX优化工作计划

## TL;DR

> **Quick Summary**: 将Agent Flow Lite前端从普通浅色主题升级为深色科技主题，提升视觉吸引力和产品专业度。包含主题系统重构、布局优化、组件视觉升级和动画效果添加。
> 
> **Deliverables**:
> - 完整的深色主题CSS变量系统
> - 重构的App.vue布局（移除重复导航）
> - 升级后的工作流编辑器（发光节点、动画连接线）
> - 现代化的聊天界面（悬浮配置面板）
> - 重新设计的知识库管理页面
> - 全新的首页设计（替换Vue默认欢迎页）
> - 通用UI组件库（Button, Card, Modal等）
> 
> **Estimated Effort**: Large (4-6 hours)
> **Parallel Execution**: YES - 3 waves
> **Critical Path**: Theme System → Layout Refactor → Page Components

---

## Context

### Original Request
用户认为当前前端页面不够美观和具备科技感，元素布局不合理，需要一个优化方案。

### Interview Summary
**Key Discussions**:
- 当前配色单一（#2c3e50深蓝色），缺乏层次感和现代感
- 导航重复：顶部导航栏和侧边栏内容重复，浪费空间
- 工作流节点样式过于简单，缺乏视觉吸引力
- 聊天界面配置栏位置突兀，打断对话流
- 首页使用Vue默认欢迎组件，与产品定位不符
- 缺少过渡动画和微交互

**Research Findings**:
- React Flow/Vue Flow支持内置深色模式 (colorMode='dark')
- 现代趋势：GitHub Dark风格背景(#0d1117) + 霓虹强调色(青色#00d4ff, 紫色#a855f7)
- 毛玻璃效果(backdrop-filter) + 发光边框创造科技感
- 连接线动画 + 网格背景增强可视化效果
- 参考：React Flow官方深色模式示例、Dribbble科技Dashboard设计

### Metis Review
**Identified Gaps** (addressed):
- 需要明确是否保留浅色主题切换功能 → 默认深色，暂不提供切换（降低复杂度）
- 需要定义具体的色彩规范 → 已在设计系统中详细定义
- 需要考虑响应式设计 → 桌面优先，移动端基础适配
- 需要明确浏览器兼容性要求 → 现代浏览器（Chrome, Firefox, Safari, Edge最新版）

---

## Work Objectives

### Core Objective
将Agent Flow Lite前端升级为深色科技主题，提升视觉吸引力和用户体验，建立统一的设计语言。

### Concrete Deliverables
1. `frontend/src/styles/theme.css` - 主题变量系统
2. `frontend/src/styles/animations.css` - 全局动画
3. `frontend/src/components/ui/` - 通用UI组件库
4. 更新的 `App.vue` - 重构布局
5. 更新的 `WorkflowView.vue` - 工作流编辑器升级
6. 更新的 `ChatTerminal.vue` - 聊天界面升级
7. 更新的 `KnowledgeView.vue` - 知识库管理升级
8. 更新的 `HomeView.vue` - 全新首页设计
9. 更新的节点组件 - StartNode, LLMNode, KnowledgeNode等

### Definition of Done
- [ ] 所有页面使用深色主题配色
- [ ] 工作流编辑器节点具有发光效果
- [ ] 聊天界面配置栏改为悬浮面板
- [ ] 首页展示产品功能而非Vue欢迎信息
- [ ] 所有交互元素有hover和active状态
- [ ] 页面切换有平滑过渡动画
- [ ] 在Chrome/Firefox/Safari中显示正常

### Must Have
- 深色主题配色系统
- App.vue布局重构（移除重复导航）
- 工作流节点视觉升级
- 聊天界面重构
- 首页重新设计

### Must NOT Have (Guardrails)
- 不添加新的UI库（保持现有依赖）
- 不修改后端API
- 不改变现有功能逻辑，仅视觉优化
- 不添加主题切换功能（Phase 2考虑）
- 不做复杂的3D效果（保持性能）

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: NO (no test framework configured)
- **User wants tests**: Manual verification only
- **QA approach**: Manual verification with visual checks

### Automated Verification (Agent-Executable)

**For Frontend/UI changes** (using playwright browser):
```
# Agent executes via playwright browser automation:
1. Navigate to: http://localhost:5173
2. Screenshot: .sisyphus/evidence/homepage.png
3. Navigate to: http://localhost:5173/workflow
4. Screenshot: .sisyphus/evidence/workflow.png
5. Navigate to: http://localhost:5173/chat
6. Screenshot: .sisyphus/evidence/chat.png
7. Navigate to: http://localhost:5173/knowledge
8. Screenshot: .sisyphus/evidence/knowledge.png
```

**Visual Verification Checklist**:
- [ ] 页面背景为深色（#0d1117或类似）
- [ ] 文字对比度足够，清晰可读
- [ ] 侧边栏有毛玻璃效果
- [ ] 工作流节点有彩色发光边框
- [ ] 按钮有hover状态变化

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Foundation - Start Immediately):
├── Task 1: Create theme.css with CSS variables
├── Task 2: Create animations.css
└── Task 3: Create UI component library

Wave 2 (Layout & Core Pages - After Wave 1):
├── Task 4: Refactor App.vue layout
├── Task 5: Redesign HomeView.vue
└── Task 6: Upgrade WorkflowView.vue

Wave 3 (Feature Pages - After Wave 2):
├── Task 7: Upgrade ChatTerminal.vue
├── Task 8: Upgrade KnowledgeView.vue
└── Task 9: Upgrade node components

Wave 4 (Polish - After Wave 3):
└── Task 10: Final polish and verification
```

### Dependency Matrix

| Task | Depends On | Blocks | Can Parallelize With |
|------|------------|--------|---------------------|
| 1 | None | 4,5,6,7,8,9 | 2, 3 |
| 2 | None | 4,5,6,7,8,9 | 1, 3 |
| 3 | None | 4,5,6,7,8,9 | 1, 2 |
| 4 | 1,2,3 | 5,6,7,8,9 | None |
| 5 | 1,2,3,4 | 10 | 6 |
| 6 | 1,2,3,4 | 10 | 5 |
| 7 | 1,2,3,4 | 10 | 8 |
| 8 | 1,2,3,4 | 10 | 7 |
| 9 | 1,2,3,4 | 10 | 7,8 |
| 10 | 5,6,7,8,9 | None | None |

### Agent Dispatch Summary

| Wave | Tasks | Recommended Agents |
|------|-------|-------------------|
| 1 | 1, 2, 3 | delegate_task(category="visual-engineering", load_skills=["frontend-ui-ux"], run_in_background=true) |
| 2 | 4, 5, 6 | dispatch parallel after Wave 1 completes |
| 3 | 7, 8, 9 | dispatch parallel after Wave 2 completes |
| 4 | 10 | final verification task |

---

## TODOs

- [ ] 1. Create theme.css - CSS variable system

  **What to do**:
  - Create `frontend/src/styles/theme.css`
  - Define CSS custom properties for colors, spacing, typography
  - Include dark theme variables (GitHub Dark inspired)
  - Define neon accent colors (cyan, purple, green)

  **Must NOT do**:
  - Do not use SCSS/Sass (keep plain CSS)
  - Do not add light theme variables yet
  - Do not modify existing files yet

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: Frontend styling and design system work
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: CSS architecture and design tokens

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3)
  - **Blocks**: Tasks 4-9
  - **Blocked By**: None

  **References**:
  - `frontend/src/assets/base.css` - Current base styles
  - GitHub Dark theme colors: #0d1117, #161b22, #21262d
  - Neon accents: #00d4ff (cyan), #a855f7 (purple)

  **Acceptance Criteria**:
  - [ ] File created at `frontend/src/styles/theme.css`
  - [ ] Contains :root with all CSS variables
  - [ ] Variables include: bg-primary, bg-secondary, accent-cyan, accent-purple, text-primary, text-secondary
  - [ ] Can be imported in main.ts

  **Commit**: YES
  - Message: `feat(ui): add dark theme CSS variable system`
  - Files: `frontend/src/styles/theme.css`

---

- [ ] 2. Create animations.css - Global animations

  **What to do**:
  - Create `frontend/src/styles/animations.css`
  - Define keyframe animations (fadeIn, slideIn, pulse, glow)
  - Add transition utilities
  - Define animation timing functions

  **Must NOT do**:
  - Do not add heavy 3D animations
  - Do not use JavaScript for animations

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Tasks 4-9
  - **Blocked By**: None

  **References**:
  - CSS animations best practices
  - Performance: use transform and opacity only

  **Acceptance Criteria**:
  - [ ] File created at `frontend/src/styles/animations.css`
  - [ ] Contains keyframes for: fadeIn, slideInUp, pulse, glow
  - [ ] Contains utility classes: .animate-fade-in, .animate-slide-up
  - [ ] Can be imported in main.ts

  **Commit**: YES
  - Message: `feat(ui): add global animation utilities`
  - Files: `frontend/src/styles/animations.css`

---

- [ ] 3. Create UI component library

  **What to do**:
  - Create `frontend/src/components/ui/` directory
  - Create Button.vue, Card.vue, Modal.vue, Input.vue
  - Components use theme.css variables
  - Support dark theme by default

  **Must NOT do**:
  - Do not add external UI libraries
  - Do not over-engineer (keep simple)

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Tasks 4-9
  - **Blocked By**: None

  **References**:
  - `frontend/src/components/WelcomeItem.vue` - Current component pattern
  - Vue 3 script setup syntax

  **Acceptance Criteria**:
  - [ ] Directory created: `frontend/src/components/ui/`
  - [ ] Button.vue with variants: primary, secondary, danger
  - [ ] Card.vue with glassmorphism effect
  - [ ] Modal.vue with backdrop blur
  - [ ] Input.vue with focus states

  **Commit**: YES
  - Message: `feat(ui): add reusable UI component library`
  - Files: `frontend/src/components/ui/*.vue`

---

- [ ] 4. Refactor App.vue layout

  **What to do**:
  - Update `frontend/src/App.vue`
  - Remove duplicate navigation (keep sidebar only)
  - Simplify header to logo + user actions only
  - Apply dark theme styles
  - Add glassmorphism effect to sidebar

  **Must NOT do**:
  - Do not change router configuration
  - Do not modify route paths

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2
  - **Blocks**: Tasks 5-9
  - **Blocked By**: Tasks 1, 2, 3

  **References**:
  - Current `frontend/src/App.vue`
  - `frontend/src/styles/theme.css` (created in Task 1)
  - `frontend/src/styles/animations.css` (created in Task 2)

  **Acceptance Criteria**:
  - [ ] Header only shows logo and user menu
  - [ ] Sidebar has glassmorphism effect
  - [ ] Background is dark (#0d1117)
  - [ ] Navigation links have hover effects
  - [ ] Active route highlighted with accent color

  **Commit**: YES
  - Message: `feat(ui): refactor App.vue with dark theme layout`
  - Files: `frontend/src/App.vue`

---

- [ ] 5. Redesign HomeView.vue

  **What to do**:
  - Replace Vue default welcome content
  - Create product-focused landing page
  - Show feature cards: Workflow, Knowledge Base, Chat
  - Add quick start actions
  - Apply dark theme styles

  **Must NOT do**:
  - Do not link to external Vue documentation
  - Do not show development setup instructions

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Task 6)
  - **Blocks**: Task 10
  - **Blocked By**: Tasks 1-4

  **References**:
  - Current `frontend/src/views/HomeView.vue`
  - `frontend/src/components/ui/Card.vue` (created in Task 3)

  **Acceptance Criteria**:
  - [ ] Shows product name and tagline
  - [ ] Feature cards for: Workflow, Knowledge, Chat
  - [ ] Quick action buttons
  - [ ] Dark theme styling
  - [ ] Responsive layout

  **Commit**: YES
  - Message: `feat(ui): redesign homepage with product focus`
  - Files: `frontend/src/views/HomeView.vue`

---

- [ ] 6. Upgrade WorkflowView.vue

  **What to do**:
  - Update `frontend/src/views/WorkflowView.vue`
  - Enable Vue Flow dark mode
  - Update toolbar styling
  - Upgrade node appearance (Task 9)
  - Add grid background pattern

  **Must NOT do**:
  - Do not change node logic or data structure
  - Do not modify Vue Flow configuration

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Task 5)
  - **Blocks**: Task 10
  - **Blocked By**: Tasks 1-4

  **References**:
  - Current `frontend/src/views/WorkflowView.vue`
  - Vue Flow dark mode documentation
  - `frontend/src/components/nodes/*.vue`

  **Acceptance Criteria**:
  - [ ] Vue Flow uses dark mode
  - [ ] Toolbar has dark styling
  - [ ] Canvas has grid/dot background
  - [ ] Buttons use UI component library

  **Commit**: YES
  - Message: `feat(ui): upgrade workflow editor with dark theme`
  - Files: `frontend/src/views/WorkflowView.vue`

---

- [ ] 7. Upgrade ChatTerminal.vue

  **What to do**:
  - Update `frontend/src/views/ChatTerminal.vue`
  - Move config bar to floating panel
  - Update message bubble styles
  - Add typing indicator animation
  - Apply dark theme

  **Must NOT do**:
  - Do not change chat logic or API calls
  - Do not modify message data structure

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 8, 9)
  - **Blocks**: Task 10
  - **Blocked By**: Tasks 1-4

  **References**:
  - Current `frontend/src/views/ChatTerminal.vue`
  - `frontend/src/styles/animations.css` (typing indicator)

  **Acceptance Criteria**:
  - [ ] Config bar is floating panel (not fixed)
  - [ ] Message bubbles have dark theme
  - [ ] User messages use accent color
  - [ ] AI messages have glassmorphism
  - [ ] Typing indicator animated

  **Commit**: YES
  - Message: `feat(ui): upgrade chat interface with floating config`
  - Files: `frontend/src/views/ChatTerminal.vue`

---

- [ ] 8. Upgrade KnowledgeView.vue

  **What to do**:
  - Update `frontend/src/views/KnowledgeView.vue`
  - Redesign knowledge base cards
  - Update upload area styling
  - Apply dark theme to document table
  - Add hover effects

  **Must NOT do**:
  - Do not change upload logic
  - Do not modify API calls

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 7, 9)
  - **Blocks**: Task 10
  - **Blocked By**: Tasks 1-4

  **References**:
  - Current `frontend/src/views/KnowledgeView.vue`
  - `frontend/src/components/ui/Card.vue`

  **Acceptance Criteria**:
  - [ ] Knowledge cards have glassmorphism
  - [ ] Upload area has dashed border + hover effect
  - [ ] Document table has dark theme
  - [ ] Progress bars use accent colors

  **Commit**: YES
  - Message: `feat(ui): upgrade knowledge base management UI`
  - Files: `frontend/src/views/KnowledgeView.vue`

---

- [ ] 9. Upgrade node components

  **What to do**:
  - Update all node components in `frontend/src/components/nodes/`
  - Add glowing border effects
  - Use theme colors for each node type
  - Add hover animations
  - Update icons (use Lucide or similar)

  **Components to update**:
  - StartNode.vue
  - LLMNode.vue
  - KnowledgeNode.vue
  - EndNode.vue
  - ConditionNode.vue

  **Must NOT do**:
  - Do not change node logic
  - Do not modify Handle positions

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 7, 8)
  - **Blocks**: Task 10
  - **Blocked By**: Tasks 1-4

  **References**:
  - Current node components in `frontend/src/components/nodes/`
  - `frontend/src/styles/theme.css`
  - CSS box-shadow for glow effects

  **Acceptance Criteria**:
  - [ ] StartNode: green glow (#22c55e)
  - [ ] LLMNode: purple glow (#a855f7)
  - [ ] KnowledgeNode: blue glow (#3b82f6)
  - [ ] EndNode: gray/red glow
  - [ ] All nodes have hover scale effect

  **Commit**: YES
  - Message: `feat(ui): add glowing effects to workflow nodes`
  - Files: `frontend/src/components/nodes/*.vue`

---

- [ ] 10. Final polish and verification

  **What to do**:
  - Update `frontend/src/main.ts` to import new styles
  - Run linter and type-check
  - Verify all pages in browser
  - Take screenshots for evidence
  - Check responsive behavior

  **Must NOT do**:
  - Do not skip linting
  - Do not commit with errors

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4
  - **Blocks**: None
  - **Blocked By**: Tasks 5-9

  **References**:
  - `frontend/src/main.ts`
  - `frontend/package.json` scripts

  **Acceptance Criteria**:
  - [ ] `npm run lint` passes
  - [ ] `npm run type-check` passes
  - [ ] All pages display correctly
  - [ ] Screenshots saved to `.sisyphus/evidence/`
  - [ ] No console errors

  **Commit**: YES
  - Message: `feat(ui): integrate theme system and finalize styling`
  - Files: `frontend/src/main.ts`, any fixes

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 1 | `feat(ui): add dark theme CSS variable system` | theme.css | File exists |
| 2 | `feat(ui): add global animation utilities` | animations.css | File exists |
| 3 | `feat(ui): add reusable UI component library` | ui/*.vue | Components render |
| 4 | `feat(ui): refactor App.vue with dark theme layout` | App.vue | Layout correct |
| 5 | `feat(ui): redesign homepage with product focus` | HomeView.vue | Page displays |
| 6 | `feat(ui): upgrade workflow editor with dark theme` | WorkflowView.vue | Canvas dark |
| 7 | `feat(ui): upgrade chat interface with floating config` | ChatTerminal.vue | Config floating |
| 8 | `feat(ui): upgrade knowledge base management UI` | KnowledgeView.vue | Cards styled |
| 9 | `feat(ui): add glowing effects to workflow nodes` | nodes/*.vue | Nodes glow |
| 10 | `feat(ui): integrate theme system and finalize styling` | main.ts | All works |

---

## Success Criteria

### Verification Commands
```bash
cd frontend
npm run lint        # Expected: no errors
npm run type-check  # Expected: no errors
npm run build       # Expected: build succeeds
```

### Visual Checklist
- [ ] Homepage shows product features
- [ ] Sidebar has glassmorphism effect
- [ ] Workflow nodes have colored glow
- [ ] Chat config is floating panel
- [ ] Knowledge cards have hover effects
- [ ] All text is readable on dark background
- [ ] Buttons have hover states
- [ ] Page transitions are smooth

### Browser Testing
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)

---

## Design Specifications

### Color Palette
```css
/* Background */
--bg-primary: #0d1117;        /* Main background */
--bg-secondary: #161b22;      /* Card/panel background */
--bg-tertiary: #21262d;       /* Input/button background */
--bg-elevated: #30363d;       /* Elevated elements */

/* Accent Colors */
--accent-cyan: #00d4ff;       /* Primary accent */
--accent-purple: #a855f7;     /* Secondary accent */
--accent-green: #22c55e;      /* Success */
--accent-orange: #f97316;     /* Warning */
--accent-red: #ef4444;        /* Error */

/* Text */
--text-primary: #e6edf3;      /* Main text */
--text-secondary: #8b949e;    /* Secondary text */
--text-muted: #6e7681;        /* Disabled/hint */

/* Border */
--border-default: #30363d;
--border-hover: #8b949e;
```

### Typography
- Font family: system-ui, -apple-system, sans-serif
- Code font: 'JetBrains Mono', 'Fira Code', monospace
- Base size: 14px

### Spacing
- Base unit: 4px
- Card padding: 16px-24px
- Section gap: 24px-32px

### Effects
- Glassmorphism: `backdrop-filter: blur(10px); background: rgba(22, 27, 34, 0.8);`
- Glow: `box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);`
- Border radius: 8px (cards), 6px (buttons), 12px (modals)

---

## Notes

### Browser Compatibility
- Target: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- backdrop-filter: Use with fallback
- CSS variables: Well supported in target browsers

### Performance Considerations
- Use transform/opacity for animations
- Avoid heavy blur on large areas
- Lazy load non-critical animations

### Future Enhancements (Phase 2)
- Theme toggle (light/dark/system)
- Custom accent color picker
- Animation intensity settings
- Mobile-responsive improvements
