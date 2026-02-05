# Decisions

## [Session Start] Task: skill-menu-home
Planning session initiated. No decisions yet.
# Task 1: Add Skill Management card to HomeView (TDD)

## Architectural Decisions

### Icon Design Choice
**Decision**: Used circular plus SVG design for skill icon
**Rationale**: 
- Visually distinct from existing icons (workflow grid, knowledge book, chat bubble)
- Represents "adding" or "skills" capability
- Simple, clean design matching existing icon style (24x24 viewBox, 2px stroke)

### Color Scheme
**Decision**: Used orange accent (#f97316) for skill icon
**Rationale**:
- Distinct from existing colors (cyan, purple, green)
- Follows inline rgba() pattern from chat icon
- Orange conveys "action/energy" appropriate for skills

### Feature Description
**Decision**: "管理 Agent Skills，封装可复用的 AI 能力"
**Rationale**:
- Matches existing description style (Chinese, descriptive)
- Clearly communicates purpose (managing skills, encapsulating capabilities)
- "Agent Skills" term already used in codebase (SkillsView.vue)

### CSS Implementation
**Decision**: Added inline rgba() values instead of new CSS variables
**Rationale**:
- Follows existing pattern from chat icon style
- Avoids adding unnecessary global CSS variables
- Maintains consistency with codebase conventions

### Test Router Route
**Decision**: Added `/skills` route to test router
**Rationale**:
- HomeView navigates to `/skills` when Skill Management card is clicked
- Test router must include all routes for proper navigation testing
- Mock component sufficient for route not under test

### Feature Union Type Extension
**Decision**: Extended existing `Feature.icon` type instead of creating new interface
**Rationale**:
- Maintains existing code structure
- Single source of truth for feature icon types
- Type-safe icon implementation
