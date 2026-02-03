# Vue Flow Theming, Background Patterns & Dark Styling

## Official Documentation Sources

- **Theming Guide**: https://vueflow.dev/guide/theming.html
- **Background Component**: https://vueflow.dev/guide/components/background.html
- **Background Props API**: https://vueflow.dev/typedocs/interfaces/BackgroundProps.html
- **BackgroundVariant Enum**: https://vueflow.dev/typedocs/enumerations/BackgroundVariant.html
- **CSS Vars Type**: https://vueflow.dev/typedocs/type-aliases/CSSVars.html
- **CustomThemeVars Interface**: https://vueflow.dev/typedocs/interfaces/CustomThemeVars.html

---

## 1. Library Styles Setup

### Required Imports
```css
/* These are necessary styles for Vue Flow */
@import '@vue-flow/core/dist/style.css';

/* This contains the default theme (optional) */
@import '@vue-flow/core/dist/theme-default.css';
```

**Key Point**: The `theme-default.css` is optional - you can build your own theme from scratch.

---

## 2. Background Component

### Installation
```bash
yarn add @vue-flow/background
# or
npm install @vue-flow/background
```

### Basic Usage
```vue
<script setup>
import { VueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
</script>

<template>
  <VueFlow>
    <Background />
  </VueFlow>
</template>
```

### Background Props

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `variant` | `"dots" \| "lines"` | `"dots"` | Pattern variant |
| `gap` | `number \| number[]` | `10` | Pattern gap |
| `size` | `number` | `0.4` | Pattern size |
| `color` | `string` | `"#81818a"` | Pattern color (replaces deprecated `patternColor`) |
| `bgColor` | `string` | `"#fff"` | Background color (deprecated - assign to `<VueFlow />` instead) |
| `lineWidth` | `number` | - | Line width for lines variant |
| `offset` | `number \| [number, number]` | `0` | Background offset |
| `x` | `number` | `0` | X-coordinate offset |
| `y` | `number` | `0` | Y-coordinate offset |

**Deprecated Props**:
- `bgColor`: Will be removed in next major version. Use `<VueFlow :style="{ background: '...' }" />` instead.
- `patternColor`: Use `color` instead.
- `height` / `width`: Deprecated, no longer needed.

### Background Variant Types
```typescript
// BackgroundVariant enum (deprecated - use string literals)
enum BackgroundVariant {
  Dots = "dots",
  Lines = "lines"
}

// Modern usage - just use string literals
type BackgroundVariantType = "lines" | "dots"
```

---

## 3. CSS Variables for Theming

### Available CSS Variables

| Variable | Effect |
|----------|--------|
| `--vf-node-color` | Defines node border, box-shadow, and handle colors |
| `--vf-box-shadow` | Defines color of node box-shadow |
| `--vf-node-bg` | Defines node background color |
| `--vf-node-text` | Defines node text color |
| `--vf-handle` | Defines node handle color |
| `--vf-connection-path` | Defines connection line color |

### Global CSS Variables Usage
```css
:root {
  --vf-node-bg: #fff;
  --vf-node-text: #222;
  --vf-connection-path: #b1b1b7;
  --vf-handle: #555;
}
```

### Per-Node CSS Variables
```javascript
const nodes = ref([
  { 
    id: '1', 
    position: { x: 100, y: 100 }, 
    data: { label: 'Node 1' },
    /* Override --vf-node-color for this specific node */
    style: { '--vf-node-color': 'blue' } 
  },
])
```

### Type Definition
```typescript
type CSSVars = 
  | "--vf-node-color" 
  | "--vf-box-shadow" 
  | "--vf-node-bg" 
  | "--vf-node-text" 
  | "--vf-connection-path" 
  | "--vf-handle"
```

---

## 4. Dark Mode Implementation Strategy

### Approach 1: CSS Variables with Data Attribute
```css
/* Light mode (default) */
:root {
  --vf-node-bg: #ffffff;
  --vf-node-text: #222222;
  --vf-connection-path: #b1b1b7;
  --vf-handle: #555555;
  --vf-node-color: #1a192b;
  --background-pattern-color: #81818a;
}

/* Dark mode */
[data-theme="dark"] {
  --vf-node-bg: #1a192b;
  --vf-node-text: #ffffff;
  --vf-connection-path: #636363;
  --vf-handle: #888888;
  --vf-node-color: #ffffff;
  --background-pattern-color: #4a4a5a;
}
```

### Approach 2: VueUse useDark Integration
```vue
<script setup>
import { useDark, useToggle } from '@vueuse/core'
import { VueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'

const isDark = useDark({
  selector: 'html',
  attribute: 'data-theme',
  valueDark: 'dark',
  valueLight: 'light'
})

const toggleDark = useToggle(isDark)
</script>

<template>
  <VueFlow :class="{ 'dark-mode': isDark }">
    <Background 
      :color="isDark ? '#4a4a5a' : '#81818a'"
      :variant="'dots'"
    />
  </VueFlow>
</template>
```

### Approach 3: Component-Level Styling
```vue
<template>
  <VueFlow 
    :style="{ 
      background: isDark ? '#1a192b' : '#ffffff' 
    }"
  >
    <Background 
      :color="isDark ? '#4a4a5a' : '#81818a'"
      :variant="isDark ? 'lines' : 'dots'"
      :gap="20"
    />
  </VueFlow>
</template>
```

---

## 5. CSS Class Names Reference

### Container Classes
| Class | Description |
|-------|-------------|
| `.vue-flow` | Outer container |
| `.vue-flow__container` | Wrapper for container elements |
| `.vue-flow__viewport` | Inner container |
| `.vue-flow__background` | Background component |
| `.vue-flow__minimap` | MiniMap component |
| `.vue-flow__controls` | Controls component |

### Node Classes
| Class | Description |
|-------|-------------|
| `.vue-flow__nodes` | Rendering wrapper around nodes |
| `.vue-flow__node` | Wrapper around each node element |
| `.vue-flow__node.selected` | Currently selected node(s) |
| `.vue-flow__node-{type}` | Node type (custom or default) |
| `.vue-flow__nodesselection` | Selection rectangle for nodes |

### Edge Classes
| Class | Description |
|-------|-------------|
| `.vue-flow__edges` | Wrapper rendering edges |
| `.vue-flow__edge` | Wrapper around each edge element |
| `.vue-flow__edge.selected` | Currently selected edge(s) |
| `.vue-flow__edge.animated` | Animated edge |
| `.vue-flow__edge-path` | SVG path for edge elements |
| `.vue-flow__connection-path` | SVG path for connection line |

### Handle Classes
| Class | Description |
|-------|-------------|
| `.vue-flow__handle` | Wrapper around node handle elements |
| `.vue-flow__handle-{position}` | Handle position (top/bottom/left/right) |
| `.vue-flow__handle-connecting` | Connection line is over the handle |
| `.vue-flow__handle-valid` | Connection line over handle with valid connection |

---

## 6. Styling Patterns

### Custom Node Class Example
```css
/* Purple custom node theme */
.vue-flow__node-custom {
  background: purple;
  color: white;
  border: 1px solid purple;
  border-radius: 4px;
  box-shadow: 0 0 0 1px purple;
  padding: 8px;
}
```

### Direct VueFlow Styling
```vue
<VueFlow
  :nodes="nodes"
  :edges="edges"
  class="my-diagram-class"  
  :style="{ background: 'red' }"
/>
```

### Node/Edge Style Objects
```javascript
const nodes = ref([
  { 
    id: '1', 
    position: { x: 250, y: 5 },
    data: { label: 'Node 1' },
    class: 'my-custom-node-class',
    style: { 
      backgroundColor: 'green', 
      width: '200px', 
      height: '100px' 
    },
  },
])
```

---

## 7. Dark Mode Best Practices

1. **Use CSS Variables**: Define all theme colors as CSS variables for easy switching
2. **Background Pattern**: Adjust background pattern color for dark mode visibility
3. **Contrast**: Ensure node/edge colors have sufficient contrast in both modes
4. **Connection Lines**: Use lighter colors for connection paths in dark mode
5. **Handle Visibility**: Ensure handles remain visible against dark backgrounds
6. **Consistency**: Apply dark mode to all Vue Flow components (Minimap, Controls)

---

## 8. Custom Theme Variables Interface

```typescript
interface CustomThemeVars {
  [key: string]: string | number | undefined
}
```

This allows extending Vue Flow's theming with custom CSS variables beyond the built-in ones.


---

## 9. Vue Flow Implementation in agent-flow-lite (Actual Codebase Findings)

### 9.1 Dependencies

**Location**: `frontend/package.json`

```json
{
  "@vue-flow/background": "^1.3.2",
  "@vue-flow/controls": "^1.1.3",
  "@vue-flow/core": "^1.48.2"
}
```

**Key Finding**: Project uses:
- `@vue-flow/core` v1.48.2 (latest major version)
- `@vue-flow/background` v1.3.2 (for background patterns)
- `@vue-flow/controls` v1.1.3 (for zoom/fit controls)
- No `@vue-flow/minimap` installed (not used)

### 9.2 Main Workflow Components

#### WorkflowEditor.vue (Primary Implementation)
**Location**: `frontend/src/views/WorkflowEditor.vue`

**Vue Flow Imports**:
```typescript
import { VueFlow, useVueFlow, Handle, Position, type Connection } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
```

**Required CSS Imports**:
```typescript
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
```

**Vue Flow Component Usage**:
```vue
<VueFlow
  v-model="elements"
  :default-zoom="1"
  :min-zoom="0.2"
  :max-zoom="4"
  :default-edge-options="{ type: 'smoothstep', animated: true }"
  :delete-key-code="'Delete'"
  @dragover="onDragOver"
  @drop="onDrop"
  @node-click="onNodeClick"
  @edge-click="onEdgeClick"
  @connect="onConnect"
  fit-view-on-init
>
```

**Custom Node Templates** (Lines 98-121):
```vue
<template #node-start="props">
  <StartNode v-bind="props" />
  <Handle type="source" :position="Position.Right" />
</template>

<template #node-llm="props">
  <LLMNode v-bind="props" />
  <Handle type="target" :position="Position.Left" />
  <Handle type="source" :position="Position.Right" />
</template>

<template #node-knowledge="props">
  <KnowledgeNode v-bind="props" />
  <Handle type="target" :position="Position.Left" />
  <Handle type="source" :position="Position.Right" />
</template>

<template #node-end="props">
  <EndNode v-bind="props" />
</template>

<template #node-condition="props">
  <ConditionNode v-bind="props" />
</template>
```

**Background Configuration** (Line 92):
```vue
<Background pattern-color="#e5e7eb" :gap="20" />
```

**Controls Component** (Line 95):
```vue
<Controls />
```

**useVueFlow Hook Usage** (Line 213):
```typescript
const { addNodes, addEdges, project, toObject, setNodes, setEdges, getNodes, getEdges, updateNode, removeNodes, removeEdges } = useVueFlow()
```

#### WorkflowView.vue (Secondary Implementation)
**Location**: `frontend/src/views/WorkflowView.vue`

**Simplified Usage**:
- Uses same imports and CSS
- Less feature-rich than WorkflowEditor
- No drag-and-drop support
- No edge customization
- Limited to 3 node types (start, llm, knowledge)
- No condition or end nodes

### 9.3 Custom Node Components

#### Node Component Files
All located in `frontend/src/components/nodes/`:

1. **StartNode.vue** (59 lines)
   - Type: `start`
   - Handles: Source (Right position only)
   - Styling: Green gradient (#10b981 to #059669)
   - Props: None (static display)
   - Uses `inheritAttrs: false`

2. **LLMNode.vue** (59 lines)
   - Type: `llm`
   - Handles: Target (Left) + Source (Right)
   - Styling: Purple gradient (#8b5cf6 to #7c3aed)
   - Props: None (static display)
   - Uses `inheritAttrs: false`

3. **KnowledgeNode.vue** (59 lines)
   - Type: `knowledge`
   - Handles: Target (Left) + Source (Right)
   - Styling: Blue gradient (#3b82f6 to #2563eb)
   - Props: None (static display)
   - Uses `inheritAttrs: false`

4. **EndNode.vue** (60 lines)
   - Type: `end`
   - Handles: Target (Left only)
   - Styling: Red gradient (#ef4444 to #dc2626)
   - Props: None (static display)
   - Uses `inheritAttrs: false`

5. **ConditionNode.vue** (93 lines)
   - Type: `condition`
   - Handles: Target (Left) + Source (Right - id="true") + Source (Bottom - id="false")
   - Styling: Orange gradient (#f59e0b to #d97706)
   - Props: `data.expression` (optional)
   - Uses `inheritAttrs: false`
   - Custom handle styling with `.handle-true` and `.handle-false` classes

#### Common Node Patterns
All nodes follow this structure:
- Template: `.node {node-type}-node` wrapper
- Header: Icon + Title
- Body: Description
- Handles: Imported from `@vue-flow/core`
- Styles: Scoped CSS with gradient backgrounds
- Box shadow: `0 4px 6px -1px rgba(0, 0, 0, 0.1)`
- Border radius: 8px
- Min width: 140-160px
- Text color: White

### 9.4 Node Configuration Panel

**Location**: `frontend/src/components/NodeConfigPanel.vue`

**Features**:
- Fixed right sidebar (360px width)
- Conditional rendering based on `nodeType`
- Supports 5 node types:
  - **Start**: `inputVariable` field
  - **LLM**: `systemPrompt` (textarea) + `temperature` (slider 0-1)
  - **Knowledge**: `knowledgeBaseId` (select dropdown)
  - **End**: `outputVariable` field
  - **Condition**: `expression` (JavaScript condition)

**API Integration**:
- Loads knowledge bases from `/api/v1/knowledge/`
- Emits events: `close`, `save`, `delete`

### 9.5 Vue Flow CSS Styling

#### Global Styles (WorkflowEditor.vue)
Lines 798-813:
```css
:deep(.vue-flow__node) {
  border: none;
  background: transparent;
  padding: 0;
}

:deep(.vue-flow__handle) {
  width: 8px;
  height: 8px;
  background: #6b7280;
  border: 2px solid white;
}

:deep(.vue-flow__handle:hover) {
  background: #3b82f6;
}
```

#### WorkflowView.vue Global Styles
Lines 282-284:
```css
:deep(.vue-flow) {
  height: 100%;
}
```

### 9.6 Event Handlers

#### WorkflowEditor.vue Event Handlers
- `@dragover`: Call `onDragOver` - enables drop
- `@drop`: Call `onDrop` - adds new nodes
- `@node-click`: Call `onNodeClick` - opens config panel
- `@edge-click`: Call `onEdgeClick` - confirms edge deletion
- `@connect`: Call `onConnect` - creates new edges

#### WorkflowView.vue Event Handlers
- `@node-click`: Call `onNodeClick` - opens config panel
- No edge or drop handlers

### 9.7 Node Data Structure

**Default Initial State** (WorkflowEditor.vue, Lines 249-256):
```typescript
const elements = ref([
  {
    id: '1',
    type: 'start',
    label: '开始',
    position: { x: 100, y: 100 },
  },
])
```

**Node Object Structure**:
```typescript
{
  id: string,
  type: 'start' | 'llm' | 'knowledge' | 'end' | 'condition',
  position: { x: number, y: number },
  label: string,
  data: {
    inputVariable?: string,
    systemPrompt?: string,
    temperature?: number,
    knowledgeBaseId?: string,
    outputVariable?: string,
    expression?: string
  }
}
```

**Edge Object Structure**:
```typescript
{
  id: string,
  source: string,
  target: string,
  sourceHandle?: string,
  targetHandle?: string,
  type?: 'smoothstep',
  animated?: boolean
}
```

### 9.8 Key Functions

**WorkflowEditor.vue**:
- `onConnect()`: Creates edge with ID format `e{source}-{target}-{sourceHandle}-{targetHandle}`
- `saveWorkflow()`: Serializes to `toObject()`, calls API `PUT /api/v1/workflows/{id}`
- `loadWorkflow()`: Loads from API, calls `setNodes()` and `setEdges()`
- `onDragStart()`: Sets `application/vueflow` data transfer type
- `onDrop()`: Uses `project()` to convert screen coords to canvas coords
- `addNodeFromPanel()`: Adds nodes at fixed offset position
- `deleteNode()`: Calls `removeNodes()`
- `saveNodeConfig()`: Calls `updateNode()` with new data

**WorkflowView.vue**:
- `addStartNode()`, `addLLMNode()`, `addKnowledgeNode()`: Add nodes with ID counter
- `saveNodeConfig()`: Direct array manipulation with spread
- `saveWorkflow()`: Calls API `POST /api/v1/workflows/`

### 9.9 Missing/Minimap Not Used

**Finding**: No `@vue-flow/minimap` package installed or used
- Minimap not imported in any component
- No `<MiniMap>` component usage
- Not in package.json dependencies

**Recommendation**: If needed for large workflows, install and add:
```bash
npm install @vue-flow/minimap
```

Then import and use:
```typescript
import { MiniMap } from '@vue-flow/minimap'
<MiniMap />
```

### 9.10 Styling Summary

**Color Scheme**:
- Background: `#f3f4f6` (light gray)
- Node Panel: `#f9fafb` (lighter gray)
- Panel Border: `#e5e7eb` (subtle gray)
- Button Primary: `#2c3e50` (dark blue-gray

---

## 10. Global Animations CSS

**Location**: `frontend/src/styles/animations.css`

Created a comprehensive animations utility file with:
- 12 keyframe animations (fadeIn, fadeInUp, fadeInDown, slideInUp, slideInDown, slideInLeft, slideInRight, scaleIn, scaleOut, pulse, glow, shimmer, bounce, spin, shake)
- Utility classes: `.animate-fade-in`, `.animate-slide-up`, `.animate-pulse`, `.animate-glow`, etc.
- Duration modifiers: `.duration-fast`, `.duration-normal`, `.duration-slow`, `.duration-slower`
- Delay modifiers: `.delay-100` through `.delay-500`
- Stagger children: `.stagger-children` for sequential animations
- Easing modifiers: `.ease-linear`, `.ease-in`, `.ease-out`, `.ease-in-out`, `.ease-spring`
- Reduced motion support via `@media (prefers-reduced-motion: reduce)`

**Performance notes**:
- All animations use `transform` and `opacity` only (GPU-accelerated)
- No layout-triggering properties (width, height, margin, etc.)
- CSS variables for customizable duration (`--animation-duration`)
- CSS variables for glow color (`--glow-color`) and shimmer color (`--shimmer-color`)

## UI Component Library Created - 2026-02-03T06:30:08Z

Created four reusable UI components in `frontend/src/components/ui/`:

### Button.vue
- Variants: `primary`, `secondary`, `danger`
- Sizes: `sm`, `md`, `lg`
- Features: gradient backgrounds, hover effects, focus-visible ring
- CSS variables used: `--color-accent`, `--color-accent-hover`, `--color-surface-elevated`, `--color-text-primary`, `--color-border`, `--color-border-hover`, `--color-surface-hover`

### Card.vue
- Glassmorphism effect with `backdrop-filter: blur(20px) saturate(180%)`
- Fallback for browsers without backdrop-filter support
- Padding variants: `none`, `sm`, `md`, `lg`
- Hover effect with lift animation
- CSS variables used: `--color-surface`, `--color-surface-glass`, `--color-surface-solid`, `--color-border`, `--color-border-hover`

### Modal.vue
- Teleport to body for proper z-index stacking
- Backdrop blur with `@supports` fallback
- Size variants: `sm` (24rem), `md` (32rem), `lg` (48rem)
- Escape key and overlay click to close
- Header, body, and optional footer slots
- CSS variables used: `--color-surface`, `--color-surface-glass`, `--color-border`, `--color-text-primary`, `--color-text-secondary`, `--color-surface-hover`, `--color-surface-subtle`, `--color-accent`

### Input.vue
- v-model support with full event forwarding
- Label with required indicator
- Error state with inline error message
- Focus ring using accent color (`--color-accent-focus`)
- CSS variables used: `--color-text-primary`, `--color-text-secondary`, `--color-text-muted`, `--color-surface`, `--color-surface-hover`, `--color-surface-elevated`, `--color-surface-muted`, `--color-border`, `--color-border-hover`, `--color-accent`, `--color-accent-focus`, `--color-error`, `--color-error-focus`, `--color-error-bg`

### Theme CSS Variables Used Across Components

```css
/* Accent colors */
--color-accent: #3b82f6;
--color-accent-hover: #2563eb;
--color-accent-focus: rgba(59, 130, 246, 0.2);

/* Surface colors */
--color-surface: rgba(30, 30, 40, 0.6);
--color-surface-glass: rgba(30, 30, 40, 0.4);
--color-surface-solid: rgba(40, 40, 55, 0.95);
--color-surface-elevated: rgba(40, 40, 55, 0.8);
--color-surface-hover: rgba(40, 40, 55, 0.7);
--color-surface-muted: rgba(30, 30, 40, 0.4);
--color-surface-subtle: rgba(0, 0, 0, 0.2);

/* Text colors */
--color-text-primary: rgba(255, 255, 255, 0.9);
--color-text-secondary: rgba(255, 255, 255, 0.7);
--color-text-muted: rgba(255, 255, 255, 0.4);

/* Border colors */
--color-border: rgba(255, 255, 255, 0.1);
--color-border-hover: rgba(255, 255, 255, 0.2);

/* Error colors */
--color-error: #ef4444;
--color-error-focus: rgba(239, 68, 68, 0.2);
--color-error-bg: rgba(239, 68, 68, 0.1);
```

### Glassmorphism Implementation Pattern

All glassmorphism components use the `@supports` rule with fallback:

```css
@supports (backdrop-filter: blur(20px)) or (-webkit-backdrop-filter: blur(20px)) {
  .component {
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    background: var(--color-surface-glass, rgba(30, 30, 40, 0.4));
  }
}

@supports not ((backdrop-filter: blur(20px)) or (-webkit-backdrop-filter: blur(20px))) {
  .component {
    background: var(--color-surface-solid, rgba(40, 40, 55, 0.95));
  }
}
```

This ensures compatibility with Safari (webkit prefix) and browsers without backdrop-filter support.
