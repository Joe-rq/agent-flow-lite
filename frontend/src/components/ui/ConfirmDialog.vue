<script setup lang="ts">
import { useConfirmDialog } from '@/composables/useConfirmDialog'
import Button from './Button.vue'

const { state } = useConfirmDialog()

function handleConfirm() {
  state.value.resolve?.(true)
  state.value.visible = false
  state.value.resolve = null
}

function handleCancel() {
  state.value.resolve?.(false)
  state.value.visible = false
  state.value.resolve = null
}
</script>

<template>
  <Transition name="confirm">
    <div v-if="state.visible" class="fixed inset-0 z-50 flex items-center justify-content bg-black/60" @click.self="handleCancel">
      <div class="bg-card border border-border rounded-lg shadow-lg p-6 w-[400px] max-w-[90vw] mx-auto">
        <h3 class="text-lg font-semibold text-foreground mb-3">{{ state.title }}</h3>
        <p class="text-sm text-muted-foreground leading-relaxed mb-6">{{ state.message }}</p>
        <div class="flex justify-end gap-2">
          <Button variant="outline" size="sm" @click="handleCancel">取消</Button>
          <Button variant="default" size="sm" @click="handleConfirm">确认</Button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.confirm-enter-active,
.confirm-leave-active {
  transition: opacity 150ms ease;
}

.confirm-enter-from,
.confirm-leave-to {
  opacity: 0;
}
</style>
