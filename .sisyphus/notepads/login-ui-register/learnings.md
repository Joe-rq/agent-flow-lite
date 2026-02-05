
## Task: Add Register CTA on Login View

### Date: 2025-02-05

### Patterns Observed

**Component Structure:**
- LoginView uses `<script setup lang="ts">` pattern (Vue 3 Composition API)
- Form validation happens in the component's submit handler (`handleLogin`)
- Uses custom Button component with variant/size props
- Styling uses CSS custom properties (theme variables like `--space-md`, `--accent-cyan`)

**Button Component:**
- Location: `frontend/src/components/ui/Button.vue`
- Variants: 'primary' | 'secondary' | 'danger'
- Sizes: 'sm' | 'md' | 'lg'
- Primary has gradient background (cyan to purple)
- Secondary has subtle background with border

**Testing Patterns:**
- Tests use Vitest + @vue/test-utils
- Pinia store mocking via `setActivePinia(createPinia())`
- Axios mocked at module level with `vi.mock('axios')`
- Router setup required for component tests
- Tests find buttons by text content using `wrapper.findAll('button')` + `.find()`

**TDD Approach:**
1. Write failing test that asserts expected behavior
2. Run tests to confirm failure (RED)
3. Implement minimal code to make tests pass (GREEN)
4. All 18 tests pass including 2 new register CTA tests

### Implementation Notes

- Register CTA reuses same `handleLogin` function as login button
- Uses `variant="secondary"` for visual distinction from primary login button
- Both buttons share same loading state (`isLoading`)
- Added `.btn { width: 100% }` style to ensure both buttons are full-width
