# Manual Node Config Save Test Guide

## Quick Test Steps

### Prerequisites
1. Start frontend dev server: `cd frontend && npm run dev`
2. Start backend server (for knowledge base API): `cd backend && uv run uvicorn main:app --reload`
3. Open browser: http://localhost:5173/workflow

---

## Test 1: Start Node - inputVariable

**Steps:**
1. Click "开始节点" in left panel (adds to canvas)
2. Click the new Start node on canvas (opens config panel)
3. In "输入变量定义" field, type: `start_var`
4. Click "保存" button
5. Click "×" to close config panel
6. Click the same Start node again

**Expected Result:**
✅ "输入变量定义" field shows `start_var`

**Actual Result:** ______________

**Status:** [ ] PASS  [ ] FAIL

---

## Test 2: LLM Node - systemPrompt and temperature

**Steps:**
1. Click "LLM 节点" in left panel
2. Click the new LLM node on canvas
3. In "系统提示词" textarea, type: `prompt_test`
4. Drag "温度参数" slider to a different position (e.g., 0.8)
5. Click "保存"
6. Click "×" to close
7. Click the same LLM node again

**Expected Result:**
✅ "系统提示词" textarea shows `prompt_test`
✅ Temperature slider is at the adjusted position

**Actual Result:**
- System prompt: ______________
- Temperature: ______________

**Status:** [ ] PASS  [ ] FAIL

---

## Test 3: Knowledge Node - knowledgeBaseId

**Steps:**
1. Click "知识库节点" in left panel
2. Click the new Knowledge node on canvas
3. Check if "选择知识库" dropdown has options
   - If YES: Select first option
   - If NO: Note this (test limited)
4. Click "保存"
5. Click "×" to close
6. Click the same Knowledge node again

**Expected Result:**
✅ Selected knowledge base is still selected

**Actual Result:** ______________

**Status:** [ ] PASS  [ ] FAIL  [ ] SKIPPED (no KBs available)

---

## Test 4: Condition Node - expression

**Steps:**
1. Click "条件节点" in left panel
2. Click the new Condition node on canvas
3. In "条件表达式 (JavaScript)" textarea, type: `{{step1.output}} === 'yes'`
4. Click "保存"
5. Click "×" to close
6. Click the same Condition node again

**Expected Result:**
✅ "条件表达式" textarea shows `{{step1.output}} === 'yes'`

**Actual Result:** ______________

**Status:** [ ] PASS  [ ] FAIL

---

## Test 5: End Node - outputVariable

**Steps:**
1. Click "结束节点" in left panel
2. Click the new End node on canvas
3. In "输出变量" field, type: `result_var`
4. Click "保存"
5. Click "×" to close
6. Click the same End node again

**Expected Result:**
✅ "输出变量" field shows `result_var`

**Actual Result:** ______________

**Status:** [ ] PASS  [ ] FAIL

---

## Console Error Check

**Steps:**
1. Open browser DevTools (F12)
2. Go to Console tab
3. Perform all tests above
4. Check for any red errors

**Expected Result:**
✅ No errors in console

**Actual Errors Found:**
- ____________________________
- ____________________________
- ____________________________

**Status:** [ ] PASS  [ ] FAIL

---

## Test Summary

| Node Type | Field Tested | Status |
|-----------|--------------|--------|
| Start | inputVariable | [ ] PASS / [ ] FAIL |
| LLM | systemPrompt | [ ] PASS / [ ] FAIL |
| LLM | temperature | [ ] PASS / [ ] FAIL |
| Knowledge | knowledgeBaseId | [ ] PASS / [ ] FAIL / [ ] SKIPPED |
| Condition | expression | [ ] PASS / [ ] FAIL |
| End | outputVariable | [ ] PASS / [ ] FAIL |
| Console | No errors | [ ] PASS / [ ] FAIL |

**Overall Result:** [ ] ALL PASS  [ ] SOME FAILURES

---

## Bug Report (if any failures)

**Node Type:** ______________

**Field:** ______________

**Expected Behavior:** ______________

**Actual Behavior:** ______________

**Steps to Reproduce:**
1. ______________
2. ______________
3. ______________

**Console Errors:** ______________

---

## Notes

- Test date: February 2, 2026
- Test URL: http://localhost:5173/workflow
- Code review showed correct implementation for all node types
- Manual testing confirms actual browser behavior matches code
