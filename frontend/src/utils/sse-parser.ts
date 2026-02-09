/**
 * SSE Parser Utility
 *
 * A chunk-safe Server-Sent Events parser that handles:
 * - Chunk boundary issues (lines split across multiple chunks)
 * - All EOL variants (\n, \r\n, \r)
 * - Event buffering across multiple chunks
 * - Type-safe event callbacks
 */

export interface SSEEventData {
  [key: string]: unknown
}

export interface SSEEventCallbacks {
  onEvent?: (eventType: string, data: SSEEventData) => void
  onComment?: (comment: string) => void
  onDone?: () => void
  onError?: (error: Error) => void
}

/**
 * SSE Parser state
 */
interface SSEParserState {
  buffer: string        // Partial line buffer
  currentEvent: string  // Current event type
  currentData: string   // Current data field content
}

/**
 * Create a new SSE parser instance
 * Each instance maintains its own parsing state
 */
export function createSSEParser(): {
  /**
   * Parse a chunk of SSE data
   * @param chunk - Data chunk from the stream
   * @param callbacks - Event handlers
   */
  parse: (chunk: string, callbacks: SSEEventCallbacks) => void
  /**
   * Reset parser state
   */
  reset: () => void
} {
  const state: SSEParserState = {
    buffer: '',
    currentEvent: '',
    currentData: '',
  }

  /**
   * Process a complete line
   */
  function processLine(line: string, callbacks: SSEEventCallbacks): void {
    const trimmedLine = line.trim()

    // Empty line: emit the current event
    if (trimmedLine === '') {
      emitEvent(callbacks)
      return
    }

    // Comment line
    if (trimmedLine.startsWith(':')) {
      callbacks.onComment?.(trimmedLine.slice(1))
      return
    }

    // Event field
    if (trimmedLine.startsWith('event:')) {
      state.currentEvent = trimmedLine.slice(6).trim()
      return
    }

    // Data field (append with newline if not empty)
    if (trimmedLine.startsWith('data:')) {
      const dataContent = trimmedLine.slice(5).trim()
      if (dataContent === '[DONE]') {
        callbacks.onDone?.()
        emitEvent(callbacks)
        return
      }
      if (state.currentData) {
        state.currentData += '\n'
      }
      state.currentData += dataContent
      return
    }

    // Other fields (ignored for now, per SSE spec)
  }

  /**
   * Emit the current event if there's data
   */
  function emitEvent(callbacks: SSEEventCallbacks): void {
    if (state.currentData === '') {
      state.currentEvent = ''
      return
    }

    try {
      const data = JSON.parse(state.currentData) as SSEEventData
      callbacks.onEvent?.(state.currentEvent || 'message', data)
    } catch (error) {
      if (error instanceof Error) {
        callbacks.onError?.(error)
      } else {
        callbacks.onError?.(new Error(String(error)))
      }
    }

    // Reset state for next event
    state.currentEvent = ''
    state.currentData = ''
  }

  /**
   * Parse a chunk of data with line buffering
   * Handles \n, \r\n, and \r line endings correctly
   */
  function parse(chunk: string, callbacks: SSEEventCallbacks): void {
    let i = 0
    const len = chunk.length

    while (i < len) {
      const char = chunk[i]

      // Check for line endings
      if (char === '\r') {
        // \r\n or \r
        if (i + 1 < len && chunk[i + 1] === '\n') {
          i += 2 // Skip \r\n
        } else {
          i += 1 // Skip \r
        }
        // Process complete line
        processLine(state.buffer, callbacks)
        state.buffer = ''
      } else if (char === '\n') {
        // \n
        i += 1
        // Process complete line
        processLine(state.buffer, callbacks)
        state.buffer = ''
      } else {
        // Append character to buffer
        state.buffer += char
        i += 1
      }
    }
  }

  /**
   * Reset parser state
   */
  function reset(): void {
    state.buffer = ''
    state.currentEvent = ''
    state.currentData = ''
  }

  return { parse, reset }
}

/**
 * Convenience function for single-shot parsing
 * Creates a parser, parses the chunk, then cleans up
 */
export function parseSSEChunk(chunk: string, callbacks: SSEEventCallbacks): void {
  const parser = createSSEParser()
  parser.parse(chunk, callbacks)
}
