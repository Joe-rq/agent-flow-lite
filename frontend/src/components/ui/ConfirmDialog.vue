<script setup lang="ts">
import { useConfirmDialog } from '@/composables/useConfirmDialog'

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
    <div v-if="state.visible" class="confirm-overlay" @click.self="handleCancel">
      <div class="confirm-card">
        <h3 class="confirm-title">{{ state.title }}</h3>
        <p class="confirm-message">{{ state.message }}</p>
        <div class="confirm-actions">
          <button class="confirm-btn confirm-btn--cancel" @click="handleCancel">取消</button>
          <button class="confirm-btn confirm-btn--ok" @click="handleConfirm">确认</button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped src="./ConfirmDialog.css"></style>
