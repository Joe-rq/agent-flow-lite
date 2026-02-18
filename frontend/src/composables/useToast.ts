import { ref } from 'vue'

export interface Toast {
  id: number
  type: 'success' | 'error' | 'warning'
  message: string
  duration: number
}

const toasts = ref<Toast[]>([])
let nextId = 0

export function useToast() {
  function showToast(message: string, type: Toast['type'] = 'error', duration = 3000) {
    const id = nextId++
    toasts.value.push({ id, type, message, duration })
    setTimeout(() => removeToast(id), duration)
  }

  function removeToast(id: number) {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  return { toasts, showToast, removeToast }
}
