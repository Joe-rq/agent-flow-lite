<script setup lang="ts">
import { useToast } from '@/composables/useToast'

const { toasts, removeToast } = useToast()

const icons: Record<string, string> = {
  success: '\u2713',
  error: '\u2717',
  warning: '\u26A0',
}
</script>

<template>
  <TransitionGroup name="toast" tag="div" class="toast-container">
    <div
      v-for="toast in toasts"
      :key="toast.id"
      :class="['toast-item', `toast-item--${toast.type}`]"
    >
      <span class="toast-icon">{{ icons[toast.type] }}</span>
      <span class="toast-message">{{ toast.message }}</span>
      <button class="toast-close" @click="removeToast(toast.id)">&times;</button>
    </div>
  </TransitionGroup>
</template>

<style scoped src="./ToastContainer.css"></style>
