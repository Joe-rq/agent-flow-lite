<script setup lang="ts">
import { useToast } from '@/composables/useToast'

const { toasts, removeToast } = useToast()

const icons: Record<string, string> = {
  success: '\u2713',
  error: '\u2717',
  warning: '\u26A0',
}

const borderColors: Record<string, string> = {
  success: 'border-l-primary',
  error: 'border-l-destructive',
  warning: 'border-l-yellow-500',
}
</script>

<template>
  <TransitionGroup name="toast" tag="div" class="fixed top-4 right-4 z-[500] flex flex-col gap-2 pointer-events-none">
    <div
      v-for="toast in toasts"
      :key="toast.id"
      :class="[
        'flex items-center gap-2.5 px-4 py-3 min-w-[280px] max-w-[420px] rounded-md bg-card border border-border shadow-lg pointer-events-auto text-sm text-foreground leading-relaxed border-l-4',
        borderColors[toast.type]
      ]"
    >
      <span class="shrink-0 text-lg leading-none">{{ icons[toast.type] }}</span>
      <span class="flex-1 break-words">{{ toast.message }}</span>
      <button
        class="shrink-0 w-6 h-6 border-none bg-transparent text-muted-foreground cursor-pointer rounded-sm flex items-center justify-center text-base transition-colors hover:bg-muted hover:text-foreground"
        @click="removeToast(toast.id)"
      >&times;</button>
    </div>
  </TransitionGroup>
</template>

<style scoped>
.toast-enter-active {
  transition: all 250ms ease;
}

.toast-leave-active {
  transition: all 150ms ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.toast-move {
  transition: transform 250ms ease;
}
</style>
