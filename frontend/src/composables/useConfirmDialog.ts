import { ref } from 'vue'

interface ConfirmDialogState {
  visible: boolean
  title: string
  message: string
  resolve: ((value: boolean) => void) | null
}

const state = ref<ConfirmDialogState>({
  visible: false,
  title: '确认',
  message: '',
  resolve: null,
})

export function useConfirmDialog() {
  function confirmDialog(message: string, title = '确认'): Promise<boolean> {
    return new Promise<boolean>((resolve) => {
      state.value = {
        visible: true,
        title,
        message,
        resolve,
      }
    })
  }

  return { state, confirmDialog }
}
