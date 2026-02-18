import type { Ref } from 'vue'

/**
 * Standardized async operation status for CRUD composables.
 *
 * Convention:
 * - SSE/streaming operations: use `isStreaming: Ref<boolean>` (binary, OK as boolean)
 * - Single CRUD operations with one boolean: `isSaving`, `isLoading`, etc. are fine
 * - Composables with multiple async flags: prefer `status: Ref<AsyncOpStatus>` + `error: Ref<string | null>`
 */
export type AsyncOpStatus = 'idle' | 'pending' | 'error'

/** Standard shape for async operations that composables can adopt. */
export interface AsyncOpState {
  status: Ref<AsyncOpStatus>
  error: Ref<string | null>
}
