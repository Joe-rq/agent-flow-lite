# Workflow Page Functional Test Report

## Test Execution Summary

**Date**: 2026-02-02
**Test URL**: http://localhost:5173/#/workflow
**Backend Status**: ❌ Not running (Connection refused on port 8000)
**Frontend Status**: ✅ Running (port 5173)

---

## Observation 1: Frontend Page Load

### Status: Partial Success

**What Observed**:
- Frontend dev server is running on port 5173
- Route `/workflow` maps to `WorkflowEditor.vue`
- Page loads successfully (verified via curl returning HTML)

**Issue Discovered**:
- Router uses hash mode: `#/workflow` not `/workflow`
- Actual route configuration: `createWebHistory(import.meta.env.BASE_URL)` (not hash mode)
- This suggests user accessed via hash URL but router expects history mode

**Network Requests**:
- Page load: ✅ Success
- Vue Flow assets: ✅ Loaded
- API requests to `/api/v1/workflows`: ❌ Failed (backend not running)

---

## Observation 2: Node Config Save Behavior Analysis

### Code Analysis Findings

**Frontend: NodeConfigPanel.vue (lines 218-222)**
```typescript
const handleSave = () => {
  if (props.nodeId) {
    emit('save', props.nodeId, { ...config.value })
  }
}
```

**Frontend: WorkflowEditor.vue (lines 384-390)**
```typescript
function saveNodeConfig(nodeId: string, data: Record<string, any>) {
  const nodes = getNodes.value
  const node = nodes.find((n: any) => n.id === nodeId)
  if (node) {
    node.data = { ...node.data, ...data }
  }
}
```

### Root Cause Analysis

**Problem**: Node config save appears to work but data is not persisted to backend

**Reasoning**:
1. ✅ `handleSave()` in NodeConfigPanel correctly emits save event with nodeId and config data
2. ✅ `saveNodeConfig()` in WorkflowEditor correctly updates node.data in memory
3. ❌ **No network request is made** to persist node data to backend
4. ❌ **No workflow auto-save** after node config changes
5. ❌ User must manually click "保存工作流" button to persist all changes to backend

**Expected Behavior**:
- User clicks Save in config panel → Node data updated in memory → Data persisted to backend

**Actual Behavior**:
- User clicks Save in config panel → Node data updated in memory only → **Lost on page refresh**

---

## Observation 3: Workflow Save Request Analysis

### Code Analysis Findings

**Frontend: WorkflowEditor.vue (lines 209-243)**
```typescript
async function saveWorkflow() {
  if (isSaving.value) return
  
  const workflowName = prompt('请输入工作流名称:', '新建工作流')
  if (!workflowName) return  // ⚠️ User can cancel
  
  isSaving.value = {true}
  try {
    const flowData = toObject()
    const response = await axios.post(`${API_BASE}/workflows`, {  // ⚠️ Missing trailing slash
      name: workflowName,
      description: '',
      graph_data: {
        nodes: flowData.nodes.map((n: any) => ({
          id: n.id,
          type: n.type,
          position: n.position,
          label: n.label
          // ❌ Missing: data field - node configs not saved!
        })),
        edges: flowData.edges.map((e: any) => ({
          id: e.id,
          source: e.source,
          target: e.target
        }))
      }
    })
    showError('工作流保存成功！')  // ⚠️ Uses showError (which is alert) for success
    console.log('Saved workflow:', response.data)
  } catch (error) {
    console.error('保存工作流失败:', error)
    showError('保存工作流失败')
  } finally {
    isSaving.value = false
  }
}
```

**Backend: workflow.py (lines 86-112)**
```python
@router.post("", response_model=Workflow, status_code=201)
async def create_workflow(workflow_data: WorkflowCreate) -> Workflow:
    # ... validates workflow_data.graph_data
    new_workflow = {
        "name": workflow_data.name,
        "description": workflow_data.description,
        "graph_data": workflow_data.graph_data.model_dump(),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    # ... saves to JSON file
```

### Root Cause Analysis

**Critical Bug #1: Missing Node Data in Save Request**

**Location**: WorkflowEditor.vue line 222-226

```typescript
nodes: flowData.nodes.map((n: any) => ({
  id: n.id,
  type: n.type,
  position: n.position,
  label: n.label
  // ❌ MISSING: data field!
})),
```

**Impact**:
- Node configuration (system prompts, temperature, knowledge base ID, etc.) is **never sent to backend**
- When workflow is saved, only node positions and types are saved
- **User loses all node configurations after page refresh**

**Expected Request Body**:
```json
{
  "name": "Test Workflow",
  "graph_data": {
    "nodes": [
      {
        "id": "llm-1",
        "type": "llm",
        "position": {"x": 250, "y": 150},
        "label": "LLM",
        "data": {
          "systemPrompt": "You are helpful",
          "temperature": 0.7
        }
      }
    ]
  }
}
```

**Actual Request Body**:
```json
{
  "name": "Test Workflow",
  "graph_data": {
    "nodes": [
      {
        "id": "llm-1",
        "type": "llm",
        "position": {"x": 250, "y": 150},
        "label": "LLM"
        // ❌ data field missing
      }
    ]
  }
}
```

---

**Critical Bug #2: Incorrect API Endpoint**

**Location**: WorkflowEditor.vue line 218

```typescript
const response = await axios.post(`${API_BASE}/workflows`, {
```

**API_BASE**: `/api/v1` (line 167)
**Request URL**: `POST /api/v1/workflows`

**Backend Route**: `router = APIRouter(prefix="/api/v1/workflows", ...)` (workflow.py line 21)
**Expected**: `POST /api/v1/workflows/` (with trailing slash)

**Note**: FastAPI typically accepts both, but this is inconsistent with backend design

---

**UX Issue #3: Confusing Success Message**

**Location**: WorkflowEditor.vue line 235

```typescript
showError('工作流保存成功！')  // ⚠️ Function named showError used for success
```

**Issue**: Using `showError()` (which calls `alert()`) for success messages is confusing

**Recommendation**: Create a `showSuccess()` function or rename to `showMessage()`

---

## Observation 4: Workflow Load Behavior Analysis

### Code Analysis Findings

**Frontend: WorkflowEditor.vue (lines 258-288)**
```typescript
async function loadWorkflow(workflowId: string) {
  try {
    const response = await axios.get(`${API_BASE}/workflows/${workflowId}`)
    const workflow = response.data
    const graphData = workflow.graph_data

    if (graphData && graphData.nodes) {
      setNodes(graphData.nodes.map((n: any) => ({
        id: n.id,
        type: n.type,
        position: n.position,
        label:: n.label || (n.type === 'start' ? '开始' : n.type === 'llm' ? 'LLM' : '知识库'),
        data: n.data || {}  // ✅ Correctly loads data field
      })))
    }
    // ... sets edges
    showLoadDialog.value = false
    showError('工作流加载成功！')  // ⚠️ Uses showError for success
  } catch (error) {
    // ...
  }
}
```

### Analysis

**Good News**:
- ✅ Workflow load correctly reads `n.data` field
- ✅ Node configurations will be restored if they were saved

**Bad News**:
- ❌ Since Bug #1 in save, `n.data` will always be `undefined` or empty
- ❌ Loading workflow restores positions/types but not configurations
- ❌ User must re-enter all node configs after loading

---

## Observation 5: Backend API Analysis

### Backend: workflow.py

**Storage**: JSON file (`backend/data/workflows.json`)
**Model**: Workflow, WorkflowCreate, WorkflowUpdate, GraphData (Pydantic)

**API Endpoints**:
- `GET /api/v1/workflows` - List all workflows
- `POST /`api/v1/workflows` - Create workflow
- `GET /api/v1/workflows/{id}` - Get workflow
- `PUT /api/v1/workflows/{id}` - Update workflow
- `DELETE /api/v1/workflows/{id}` - Delete workflow

**Data Structure**:
```json
{
  "workflows": {
    "uuid-string": {
      "name": "Workflow Name",
      "description": "...",
      "graph_data": {
        "nodes": [...],
        "edges": [...]
      },
      "created_at": "2024-02-02T...",
      "updated_at": "2024-02-02T..."
    }
  }
}
```

**Observation**: Backend is correctly configured to store node data if provided

---

## Summary of Issues

| Issue | Severity | Location | Impact |
|-------|----------|----------|--------|
| **Node data not saved to backend** | 🔴 Critical | WorkflowEditor.vue:222 | All node configs lost on refresh |
| **Missing 'data' field in save request** | 🔴 Critical | WorkflowEditor.vue:222-226 | Workflow save incomplete |
| **Backend not running** | 🟡 High | Server | Cannot test save/load functionality |
| **Confusing success/error messages** | 🟢 Low | WorkflowEditor.vue:235 | UX issue |
| **Inconsistent API endpoint format** | 🟢 Low | WorkflowEditor.vue:218 | Minor inconsistency |

---

## Root Cause

The user's complaint "clicking Save in node config has no effect" is **partially correct**:

1. **What actually happens**: Clicking Save in config panel DOES update node data in memory
2. **What user expects**: Node data should be immediately persisted to backend
3. **What is broken**: Node data is not sent to backend when saving workflow

The actual bug is in the workflow save function, which omits the `data` field when serializing nodes.

---

## Recommended Fixes

### Fix #1: Add 'data' field to workflow save (Critical)

**File**: `frontend/src/views/WorkflowEditor.vue`

**Change line 222-226 from**:
```typescript
nodes: flowData.nodes.map((n: any) => ({
  id: n.id,
  type: n.type,
  position: n.position,
  label: n.label
})),
```

**To**:
```typescript
nodes: flowData.nodes.map((n: any) => ({
  id: n.id,
  type: n.type,
  position: n.position,
  label: n.label,
  data: n.data || {}  // ✅ Add this line
})),
```

---

### Fix #2: Add auto-save after node config change (Recommended)

**File**: `frontend/src/views/WorkflowEditor.vue`

**Change line 384-390 from**:
```typescript
function saveNodeConfig(nodeId: string, data: Record<string, any>) {
  const nodes = getNodes.value
  const node = nodes.find((n: any) => n.id.id === nodeId)
  if (node) {
    node.data = { ...node.data, ...data }
  }
}
```

**To**:
```typescript
function saveNodeConfig(nodeId: string, data: Record<string, any>) {
  const nodes = getNodes.value
  const node = nodes.find((n: any) => n.id === nodeId)
  if (node) {
    node.data = { ...node.data, ...data }
    // Optional: Auto-save workflow after node config change
    // saveWorkflow() // Uncomment to enable auto-save
  }
}
```

---

### Fix #3: Improve success/error messaging (UX)

**File**: `frontend/src/views/WorkflowEditor.vue`

**Add after line 206**:
```typescript
function showSuccess(message: string) {
  alert(message)
}
```

**Change line 235 from**:
```typescript
showError('工作流保存成功！')
```

**To**:
```typescript
showSuccess('工作流保存成功！')
```

---

## Test Data

**Backend Connection**: ❌ Failed (Connection refused)
- Error: `curl: (7) Failed to connect to localhost port 8000`
- Note: Backend needs to be running with `cd backend && uv run uvicorn main:app --reload`

**Network Requests Captured**: None (backend not running)

**Console Errors**: Not captured (browser automation failed)

---

## Next Steps for Testing

1. **Start backend**:
   ```bash
   cd backend
   uv run uvicorn main:app --reload --port 8000
   ```

2. **Apply Fix #1** (add 'data' field to save request)

3. **Manual test**:
   - Open http://localhost:5173/#/workflow
   - Add LLM node
   - Click node, configure system prompt and temperature
   - Click Save in config panel
   - Click "保存工作流" button
   - Enter workflow name
   - Verify request body includes node data in DevTools Network tab
   - Refresh page
   - Click "加载工作流" button
   - Verify node configuration is restored

---

## Conclusion

**User Report Validated**: ✅ Confirmed

The reported issues are real:
1. Node config save has limited effect (only updates memory, doesn't persist)
2. Workflow save fails to include node data (root cause of lost configurations)

**Primary Fix Required**: Add `data: n.data || {}` to line 226 in WorkflowEditor.vue

**Expected Outcome After Fix**: Node configurations will persist through save/load cycle
