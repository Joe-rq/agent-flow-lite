# Agent Flow Lite UI 升级方案 v2

> **适用范围**：Vue 3 + Tailwind CSS v4.2 + shadcn/ui + CVA
> **核心原则**：语义化 token 优先 · 零硬编码颜色 · 零冗余 CSS

---

## 核心改动清单

| 优先级 | 改动项 | 文件 | 说明 |
|--------|--------|------|------|
| P0 | 新增 `.flow-node-base` | `app.css` | `@layer components` 抽离节点基础样式 |
| P0 | 节点样式重写 | `nodes/*.vue` × 8 | 全彩填充 → 白底+彩条，删除 scoped style |
| P1 | Card 圆角 + 阴影增强 | `ui/Card.vue` | 保留语义 token，增强层次感 |
| P1 | Button 渐变效果 | `ui/Button.vue` | CVA default variant 升级 |

**不改动**：
- `app.css` 中的配色变量（`--color-primary` 等）和 dark mode 定义
- 任何 TypeScript 逻辑、组件 Props、Vue 组件树结构

**已知限制**：
- Button `default` variant 使用硬编码渐变（`from-cyan-600 to-blue-600`），暗色模式下不自动调整亮度

---

## Step 0: 新增节点基础样式

**文件**: `frontend/src/app.css`

在文件末尾追加：

```css
@layer components {
  .flow-node-base {
    @apply bg-card text-card-foreground rounded-xl p-3 min-w-[140px] border border-border;
  }
}
```

**设计决策**：
- `bg-card` / `text-card-foreground` / `border-border`：语义 token，自动适配暗色模式
- **不包含** `box-shadow`——各节点类型通过 Tailwind colored shadow 自行提供，实现亮/暗模式自适应
- **不包含** 子元素样式——header、icon、body 布局由各节点模板的 utility class 控制

---

## Step 1: 升级工作流节点

### 修改目标

```
修改前：                      修改后：
┌──────────────┐           ┌──────────────┐
│ ▶ 开始       │           │ ▶ 开始       │ ← 3px 顶部彩条
│ 工作流起点    │           │ 工作流起点    │
│ ████████████ │           │              │ ← bg-card（跟随主题）
└──────────────┘           └──────────────┘
  全彩渐变 + 白字              语义背景 + 彩条 + colored shadow
```

### 统一改动模式

每个节点：
1. **删除**整个 `<style scoped>` 块（ConditionNode 除外）
2. **替换**模板 class，使用 `flow-node-base` + 类型特有 utility
3. 阴影使用 Tailwind colored shadow：`shadow-lg shadow-{color}/10 dark:shadow-{color}/30`
   - 亮色模式：10% 透明度，柔和光晕
   - 暗色模式：30% 透明度，确保可见性

### 1.1 StartNode.vue

**文件**: `frontend/src/components/nodes/StartNode.vue`

**完整替换为**：

```vue
<template>
  <div class="flow-node-base border-t-[3px] border-t-emerald-500 shadow-lg shadow-emerald-500/10 dark:shadow-emerald-500/30">
    <div class="flex items-center gap-2 mb-1">
      <span class="w-5 h-5 flex items-center justify-center rounded text-xs bg-emerald-500/10 text-emerald-600">▶</span>
      <span class="text-sm font-semibold text-card-foreground">开始</span>
    </div>
    <div class="text-xs text-muted-foreground">工作流起点</div>
  </div>
</template>

<script setup lang="ts">
// Node component
</script>

<script lang="ts">
export default {
  inheritAttrs: false,
}
</script>
```

无 `<style scoped>`。

### 1.2 LLMNode.vue

**文件**: `frontend/src/components/nodes/LLMNode.vue`

**template 替换为**：

```vue
<template>
  <div class="flow-node-base border-t-[3px] border-t-violet-500 shadow-lg shadow-violet-500/10 dark:shadow-violet-500/30">
    <div class="flex items-center gap-2 mb-1">
      <span class="w-5 h-5 flex items-center justify-center rounded text-xs bg-violet-500/10 text-violet-600">🤖</span>
      <span class="text-sm font-semibold text-card-foreground">LLM</span>
    </div>
    <div class="text-xs text-muted-foreground">{{ displayText }}</div>
  </div>
</template>
```

script 保持不变，删除 `<style scoped>`。

### 1.3 KnowledgeNode.vue

**文件**: `frontend/src/components/nodes/KnowledgeNode.vue`

**template 替换为**：

```vue
<template>
  <div class="flow-node-base border-t-[3px] border-t-blue-500 shadow-lg shadow-blue-500/10 dark:shadow-blue-500/30">
    <div class="flex items-center gap-2 mb-1">
      <span class="w-5 h-5 flex items-center justify-center rounded text-xs bg-blue-500/10 text-blue-600">📚</span>
      <span class="text-sm font-semibold text-card-foreground">知识库</span>
    </div>
    <div class="text-xs text-muted-foreground">检索知识库</div>
  </div>
</template>
```

删除 `<style scoped>`。

### 1.4 SkillNode.vue

**文件**: `frontend/src/components/nodes/SkillNode.vue`

**template 替换为**：

```vue
<template>
  <div class="flow-node-base border-t-[3px] border-t-indigo-500 shadow-lg shadow-indigo-500/10 dark:shadow-indigo-500/30">
    <div class="flex items-center gap-2 mb-1">
      <span class="w-5 h-5 flex items-center justify-center rounded text-xs bg-indigo-500/10 text-indigo-600">🎯</span>
      <span class="text-sm font-semibold text-card-foreground">Skill</span>
    </div>
    <div class="text-xs text-muted-foreground truncate max-w-[120px]">{{ skillDisplayName }}</div>
  </div>
</template>
```

删除 `<style scoped>`。注意文本截断通过 `truncate max-w-[120px]` 实现。

### 1.5 HttpNode.vue

**文件**: `frontend/src/components/nodes/HttpNode.vue`

**template 替换为**：

```vue
<template>
  <div class="flow-node-base min-w-[160px] border-t-[3px] border-t-orange-500 shadow-lg shadow-orange-500/10 dark:shadow-orange-500/30">
    <div class="flex items-center gap-2 mb-1">
      <span class="w-5 h-5 flex items-center justify-center rounded text-xs bg-orange-500/10 text-orange-600">🌐</span>
      <span class="text-sm font-semibold text-card-foreground">HTTP</span>
    </div>
    <div class="text-xs text-muted-foreground truncate max-w-[140px]">{{ displayText }}</div>
  </div>
</template>
```

删除 `<style scoped>`。`min-w-[160px]` 覆盖 base 的 140px。

### 1.6 CodeNode.vue

**文件**: `frontend/src/components/nodes/CodeNode.vue`

**template 替换为**：

```vue
<template>
  <div class="flow-node-base border-t-[3px] border-t-slate-500 shadow-lg shadow-slate-500/10 dark:shadow-slate-500/30">
    <div class="flex items-center gap-2 mb-1">
      <span class="w-5 h-5 flex items-center justify-center rounded text-xs bg-slate-500/10 text-slate-600">🧪</span>
      <span class="text-sm font-semibold text-card-foreground">Code</span>
    </div>
    <div class="text-xs text-muted-foreground">{{ displayText }}</div>
  </div>
</template>
```

删除 `<style scoped>`。

### 1.7 EndNode.vue

**文件**: `frontend/src/components/nodes/EndNode.vue`

**template 替换为**：

```vue
<template>
  <div class="flow-node-base border-t-[3px] border-t-red-500 shadow-lg shadow-red-500/10 dark:shadow-red-500/30">
    <div class="flex items-center gap-2 mb-1">
      <span class="w-5 h-5 flex items-center justify-center rounded text-xs bg-red-500/10 text-red-600">⏹</span>
      <span class="text-sm font-semibold text-card-foreground">结束</span>
    </div>
    <div class="text-xs text-muted-foreground">工作流终点</div>
    <Handle type="target" :position="Position.Left" />
  </div>
</template>
```

script 保持不变（保留 Handle/Position import），删除 `<style scoped>`。

### 1.8 ConditionNode.vue（纯 utility，无 scoped style）

**文件**: `frontend/src/components/nodes/ConditionNode.vue`

ConditionNode 有 Vue Flow Handle 样式和 label 定位，通过以下方式在模板中完成，**不需要 `<style scoped>`**：
- Handle 基础样式：根 div 上使用 arbitrary variant `[&_.vue-flow__handle]:*`
- Handle label 定位：直接在 `<span>` 上使用 utility class（`absolute left-3 top-1/2 -translate-y-1/2`）

**完整替换为**：

```vue
<template>
  <div class="flow-node-base min-w-[160px] border-t-[3px] border-t-pink-500 shadow-lg shadow-pink-500/10 dark:shadow-pink-500/30
    [&_.vue-flow__handle]:w-2 [&_.vue-flow__handle]:h-2 [&_.vue-flow__handle]:bg-white [&_.vue-flow__handle]:border-2 [&_.vue-flow__handle]:border-pink-500
    [&_.handle-true]:border-emerald-500 [&_.handle-false]:border-red-500"
  >
    <div class="flex items-center gap-2 mb-1">
      <span class="w-5 h-5 flex items-center justify-center rounded text-xs bg-pink-500/10 text-pink-600">⚡</span>
      <span class="text-sm font-semibold text-card-foreground">条件</span>
    </div>
    <div class="text-xs text-muted-foreground truncate max-w-[140px]">{{ expression || '点击配置条件' }}</div>
    <Handle type="target" :position="Position.Left" />
    <Handle type="source" :position="Position.Right" id="true" class="handle-true">
      <span class="absolute left-3 top-1/2 -translate-y-1/2 text-[10px] font-semibold pointer-events-none whitespace-nowrap text-emerald-500">True</span>
    </Handle>
    <Handle type="source" :position="Position.Bottom" id="false" class="handle-false">
      <span class="absolute top-3 left-1/2 -translate-x-1/2 text-[10px] font-semibold pointer-events-none whitespace-nowrap text-red-500">False</span>
    </Handle>
  </div>
</template>
```

script 保持不变，删除 `<style scoped>`。

**Handle 样式说明**：
- `[&_.vue-flow__handle]:*`：arbitrary variant 替代 `:deep()`，穿透 Vue Flow 内部 DOM
- Handle label 的 `absolute` 定位相对于 Handle 组件（Vue Flow Handle 自身是 positioned element）

---

## Step 2: 优化 Card 组件

**文件**: `frontend/src/components/ui/Card.vue`

**修改 template 中的 class**：

```vue
<!-- 修改前 -->
<div
  :class="cn(
    'rounded-lg border border-border bg-card shadow-sm transition-all duration-300',
    paddingMap[props.padding],
    props.hover && 'hover:border-primary hover:shadow-md hover:-translate-y-0.5',
    props.class
  )"
>

<!-- 修改后 -->
<div
  :class="cn(
    'rounded-xl border border-border bg-card shadow-sm transition-all duration-300',
    paddingMap[props.padding],
    props.hover && 'hover:border-primary/30 hover:shadow-md',
    props.class
  )"
>
```

**设计决策**：
- `bg-card` / `border-border`：语义 token 不动，dark mode 自动适配
- `rounded-lg` (8px) → `rounded-xl` (12px)：适度提升
- `shadow-sm`：亮色模式柔和阴影。暗色模式不额外加阴影——`bg-card`（`#1e293b`）比 `bg-background`（`#0f172a`）亮一档已形成层级，`border-border` 提供视觉边界，黑色阴影在暗色背景上不可见，加了也没意义
- 移除 `hover:-translate-y-0.5`：避免布局抖动
- `hover:border-primary/30`：30% 透明度，比原来的实色 `hover:border-primary` 更克制

---

## Step 3: 增强 Button 渐变效果

**文件**: `frontend/src/components/ui/Button.vue`

### 修改 CVA 配置

**base class 修改**：`transition-colors` → `transition-all`（使阴影变化也有过渡效果）

**default variant 修改**：

```typescript
// 修改前
default: 'bg-primary text-primary-foreground hover:bg-primary/90',

// 修改后
default: 'bg-gradient-to-br from-cyan-600 to-blue-600 text-white shadow-md shadow-cyan-600/20 dark:shadow-cyan-500/40 hover:shadow-lg hover:shadow-cyan-600/30 hover:from-cyan-500 hover:to-blue-500',
```

其他 variant 不变。

**设计决策**：
- 渐变 `from-cyan-600 to-blue-600` 与现有 `--color-primary: #0891b2`（cyan-600）一致
- 阴影使用 Tailwind colored shadow（`shadow-cyan-600/20`，暗色 `dark:shadow-cyan-500/40`），非 arbitrary value
- hover 时渐变变亮 + 阴影增强
- **已知限制**：渐变色硬编码，暗色模式不自动调整。如需适配可追加 `dark:from-cyan-400 dark:to-blue-400`

---

## 节点修改对照表

| 节点 | 文件 | 彩条色 | Shadow (亮/暗) | 图标样式 | 特殊处理 |
|------|------|--------|---------------|----------|---------|
| Start | `StartNode.vue` | `emerald-500` | `10%` / `30%` | `bg-emerald-500/10 text-emerald-600` | — |
| LLM | `LLMNode.vue` | `violet-500` | `10%` / `30%` | `bg-violet-500/10 text-violet-600` | — |
| Knowledge | `KnowledgeNode.vue` | `blue-500` | `10%` / `30%` | `bg-blue-500/10 text-blue-600` | — |
| Skill | `SkillNode.vue` | `indigo-500` | `10%` / `30%` | `bg-indigo-500/10 text-indigo-600` | `truncate max-w-[120px]` |
| Http | `HttpNode.vue` | `orange-500` | `10%` / `30%` | `bg-orange-500/10 text-orange-600` | `min-w-[160px]` `truncate max-w-[140px]` |
| Code | `CodeNode.vue` | `slate-500` | `10%` / `30%` | `bg-slate-500/10 text-slate-600` | — |
| End | `EndNode.vue` | `red-500` | `10%` / `30%` | `bg-red-500/10 text-red-600` | 有 Handle import |
| Condition | `ConditionNode.vue` | `pink-500` | `10%` / `30%` | `bg-pink-500/10 text-pink-600` | `min-w-[160px]`, Handle arbitrary variants |

**配色变更说明**：
- ConditionNode：amber → pink（与 SkillNode 区分，原来两者同色无法辨别）
- SkillNode：amber → indigo（与 LLM 的 violet 区分，靛蓝色更契合"技能"语义）

---

## 注意事项

### 1. 不动配色变量

`app.css` 中的 `--color-primary: #0891b2` 和完整的 `.dark {}` 覆盖保持不动。

### 2. Vue Flow 画布兼容性

**禁止**在节点上添加位移类 hover 效果：
- ❌ `hover:scale-105` → 连线锚点错位
- ❌ `hover:-translate-y-1` → 节点跳动
- ✅ `hover:shadow-xl` → 仅视觉变化，不影响布局

### 3. Colored Shadow 暗色模式原理

亮色模式下 `rgba(0,0,0,0.05)` 级别的中性阴影可以营造层次感，但在暗色背景（`#0f172a`）上完全不可见。

**节点和 Button**：使用 Tailwind colored shadow + `dark:` variant 提高暗色下阴影可见性：
```
shadow-lg shadow-violet-500/10 dark:shadow-violet-500/30
```

**Card**：暗色模式下不依赖阴影。`bg-card`（`#1e293b`）比 `bg-background`（`#0f172a`）亮一档形成 surface elevation，`border-border` 提供视觉边界。这是 Material Design 3 推荐的暗色层级表达方式。

### 4. ConditionNode 的 Handle 样式

ConditionNode 使用 Tailwind arbitrary variant（`[&_.vue-flow__handle]:*`）替代传统的 `:deep()` 穿透，与其他 7 个节点保持一致——**所有 8 个节点均无 `<style scoped>`**。

Handle label 定位直接使用 utility class（`absolute left-3 top-1/2 -translate-y-1/2`），不需要自定义 CSS class。

### 5. 验证步骤

每改完一个节点：
1. 亮色模式下节点正确渲染（白底 + 彩条 + 彩色光晕）
2. 暗色模式下节点正确渲染（暗底 + 彩条 + 可见光晕）
3. 连线正常显示和跟随拖拽
4. ConditionNode 的 True/False Handle 位置和颜色正确

---

## 检查清单

- [ ] `app.css` 新增 `.flow-node-base`（`bg-card text-card-foreground border-border`，无 shadow）
- [ ] 8 个节点：全部删除 `<style scoped>`，template 使用 `flow-node-base` + colored shadow
- [ ] ConditionNode：Handle 样式通过 arbitrary variant 实现，label 用 utility class
- [ ] Card.vue：`rounded-xl` + `shadow-sm` + 移除 `hover:-translate-y` + 暗色模式靠 border/bg 层级
- [ ] Button.vue：default variant 渐变 + colored shadow（含 `dark:shadow-cyan-500/40`）+ `transition-all`
- [ ] 亮色模式全部组件视觉正确
- [ ] 暗色模式全部组件视觉正确（节点光晕可见、Card 层次分明）
- [ ] 画布拖拽和连线功能正常
- [ ] `npm run build` 通过（vue-tsc + vite）

---

**涉及文件**：`app.css` + 8 × `nodes/*.vue` + `Card.vue` + `Button.vue` = 11 个文件
**风险等级**：低（纯样式改动，不动逻辑和组件结构）
