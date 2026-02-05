/**
 * Tests for SSE event handling in SkillsView.
 *
 * Validates that handleSSEEvent correctly processes events from
 * the skill executor backend (thought, token, citation, done, error).
 */
import { describe, it, expect, vi } from 'vitest'

/**
 * Extracted SSE event handler logic matching SkillsView.vue implementation.
 * This mirrors the handleSSEEvent function to test in isolation.
 */
function handleSSEEvent(
  eventType: string,
  data: Record<string, unknown>,
  state: {
    setThought: (v: string) => void
    appendOutput: (v: string) => void
    setRunning: (v: boolean) => void
  },
) {
  switch (eventType) {
    case 'thought':
      // Bug fix: backend sends data.message/data.status, NOT data.content
      state.setThought((data.message as string) || (data.status as string) || '')
      break
    case 'token':
      state.appendOutput((data.content as string) || '')
      break
    case 'citation':
      if (data.sources && (data.sources as unknown[]).length > 0) {
        state.appendOutput(
          '\n[引用 ' + (data.sources as unknown[]).length + ' 个来源]',
        )
      }
      break
    case 'done':
      state.setRunning(false)
      state.setThought('')
      break
    case 'error':
      state.appendOutput(
        '\n[错误: ' +
          ((data.content as string) || (data.message as string) || '未知错误') +
          ']',
      )
      state.setRunning(false)
      state.setThought('')
      break
  }
}

describe('SSE Event Handler', () => {
  function createMockState() {
    return {
      setThought: vi.fn(),
      appendOutput: vi.fn(),
      setRunning: vi.fn(),
    }
  }

  describe('thought event', () => {
    it('reads message field from backend thought event', () => {
      const state = createMockState()
      handleSSEEvent(
        'thought',
        { type: 'validation', status: 'complete', message: 'All required inputs provided' },
        state,
      )
      expect(state.setThought).toHaveBeenCalledWith('All required inputs provided')
    })

    it('falls back to status when message is absent', () => {
      const state = createMockState()
      handleSSEEvent('thought', { type: 'retrieval', status: 'searching' }, state)
      expect(state.setThought).toHaveBeenCalledWith('searching')
    })

    it('sets empty string when neither message nor status exist', () => {
      const state = createMockState()
      handleSSEEvent('thought', { type: 'generation' }, state)
      expect(state.setThought).toHaveBeenCalledWith('')
    })

    it('does NOT read data.content (regression: old incorrect field)', () => {
      const state = createMockState()
      handleSSEEvent('thought', { content: 'should-be-ignored' }, state)
      // Should get empty string, not 'should-be-ignored'
      expect(state.setThought).toHaveBeenCalledWith('')
    })
  })

  describe('token event', () => {
    it('appends token content to output', () => {
      const state = createMockState()
      handleSSEEvent('token', { content: 'Hello' }, state)
      expect(state.appendOutput).toHaveBeenCalledWith('Hello')
    })

    it('handles empty content gracefully', () => {
      const state = createMockState()
      handleSSEEvent('token', {}, state)
      expect(state.appendOutput).toHaveBeenCalledWith('')
    })
  })

  describe('citation event', () => {
    it('appends citation info when sources exist', () => {
      const state = createMockState()
      handleSSEEvent(
        'citation',
        { sources: [{ doc_id: 'doc1', score: 0.9 }, { doc_id: 'doc2', score: 0.8 }] },
        state,
      )
      expect(state.appendOutput).toHaveBeenCalledWith('\n[引用 2 个来源]')
    })

    it('does nothing when sources is empty', () => {
      const state = createMockState()
      handleSSEEvent('citation', { sources: [] }, state)
      expect(state.appendOutput).not.toHaveBeenCalled()
    })
  })

  describe('done event', () => {
    it('stops running and clears thought', () => {
      const state = createMockState()
      handleSSEEvent('done', { status: 'success' }, state)
      expect(state.setRunning).toHaveBeenCalledWith(false)
      expect(state.setThought).toHaveBeenCalledWith('')
    })
  })

  describe('error event', () => {
    it('appends error message and stops running', () => {
      const state = createMockState()
      handleSSEEvent('error', { message: 'Something went wrong' }, state)
      expect(state.appendOutput).toHaveBeenCalledWith('\n[错误: Something went wrong]')
      expect(state.setRunning).toHaveBeenCalledWith(false)
      expect(state.setThought).toHaveBeenCalledWith('')
    })

    it('uses content field if message is absent', () => {
      const state = createMockState()
      handleSSEEvent('error', { content: 'Error content' }, state)
      expect(state.appendOutput).toHaveBeenCalledWith('\n[错误: Error content]')
    })

    it('shows default message when no fields present', () => {
      const state = createMockState()
      handleSSEEvent('error', {}, state)
      expect(state.appendOutput).toHaveBeenCalledWith('\n[错误: 未知错误]')
    })
  })
})
