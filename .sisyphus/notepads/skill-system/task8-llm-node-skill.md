# Task 8: LLM Node Load-Skill Support

## Summary

Implemented skill loading support for LLM nodes, allowing users to select a skill from the LLM node configuration panel. When a skill is selected, its prompt and model configuration are automatically loaded and used during execution.

## Files Created/Modified

### Backend

1. **backend/app/core/workflow_nodes.py**
   - Modified `execute_llm_node()` to support skill loading
   - When `skillName` is present in node data, loads skill from SkillLoader
   - Uses skill's prompt as system prompt (overriding node config)
   - Uses skill's model temperature (overriding node config if available)
   - Emits `skill_loaded` thought event for debugging
   - Graceful error handling when skill fails to load
   - Preserves existing behavior when no skill is selected

2. **backend/tests/test_llm_node_skill.py** (NEW)
   - 8 comprehensive tests covering:
     - LLM node without skill (existing behavior preserved)
     - LLM node with skill loading
     - Skill not found error handling
     - Skill prompt overriding node prompt
     - Skill temperature overriding node temperature
     - Skill without model config (preserves node config)
     - Template variable resolution in skill prompt
     - Empty skill name handling

### Frontend

3. **frontend/src/components/nodes/LLMNode.vue**
   - Added computed `displayText` to show selected skill name
   - Shows "Skill: {name}" when skill is selected
   - Shows "AI 模型调用" when no skill selected

4. **frontend/src/components/NodeConfigPanel.vue**
   - Added skill selection dropdown for LLM nodes
   - Added `onLLMSkillChange()` handler to load skill details
   - When skill selected, auto-populates:
     - System prompt from skill.prompt
     - Temperature from skill.model.temperature
   - Disabled prompt/temperature inputs when skill selected
   - Added skillModelConfig to node config for persistence
   - Loads skill list when LLM node config panel opens

## Key Features

1. **Skill Selection**: LLM node config panel now has a skill dropdown
2. **Auto-Load**: Selecting a skill automatically loads its prompt and model config
3. **Override Behavior**: Skill config takes precedence over node config
4. **Fallback**: When skill has no model config, node config is preserved
5. **Error Handling**: Skill load failures emit node_error event
6. **Backward Compatible**: Existing LLM nodes without skills work unchanged

## Testing

```bash
# Backend tests
cd backend && uv run pytest tests/test_llm_node_skill.py -v
# Result: 8 passed

# All backend tests
cd backend && uv run pytest tests/ -q
# Result: 185 passed

# Frontend build
cd frontend && npm run build-only
# Result: ✓ built in 692ms
```

## API Integration

- GET /api/v1/skills - Load skill list for dropdown
- GET /api/v1/skills/{name} - Load skill details (prompt + model config)
- Skill data stored in node.data.skillName
- Skill model config stored in node.data.skillModelConfig

## Verification

- [x] LLM node can select a skill from dropdown
- [x] Skill prompt is loaded and used as system prompt
- [x] Skill temperature overrides node temperature
- [x] Existing LLM nodes work without changes
- [x] All 185 backend tests pass
- [x] Frontend builds successfully
- [x] 8 new tests for LLM node skill loading

## Dependencies

- Task 2 (Skill Loader) - COMPLETED
- Task 3 (Skill Executor) - COMPLETED
- Task 6 (Workflow Skill Node) - COMPLETED
