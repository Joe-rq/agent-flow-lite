<script setup lang="ts">
interface Props {
  variant?: 'primary' | 'secondary' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  type?: 'button' | 'submit' | 'reset'
}

withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  disabled: false,
  type: 'button',
})

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

function handleClick(event: MouseEvent) {
  emit('click', event)
}
</script>

<template>
  <button
    :type="type"
    :disabled="disabled"
    :class="['btn', `btn--${variant}`, `btn--${size}`, { 'btn--disabled': disabled }]"
    @click="handleClick"
  >
    <slot />
  </button>
</template>

<style scoped>
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-family: inherit;
  font-weight: 500;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  user-select: none;
}

.btn:focus-visible {
  outline: 2px solid var(--accent-cyan, #0891b2);
  outline-offset: 2px;
}

/* Size variants */
.btn--sm {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
  height: 2rem;
}

.btn--md {
  padding: 0.5rem 1rem;
  font-size: 0.9375rem;
  height: 2.5rem;
}

.btn--lg {
  padding: 0.625rem 1.25rem;
  font-size: 1rem;
  height: 3rem;
}

/* Primary variant */
.btn--primary {
  background: linear-gradient(135deg, var(--accent-cyan, #0891b2), var(--accent-purple, #7c3aed));
  color: white;
  box-shadow: var(--shadow-sm);
}

.btn--primary:hover:not(:disabled) {
  background: linear-gradient(135deg, var(--accent-purple, #7c3aed), var(--accent-cyan, #0891b2));
  box-shadow: var(--shadow-glow-cyan);
  transform: translateY(-1px);
}

.btn--primary:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: var(--shadow-sm);
}

/* Secondary variant */
.btn--secondary {
  background: var(--bg-tertiary, #f1f5f9);
  color: var(--text-primary, #0f172a);
  border: 1px solid var(--border-primary, rgba(148, 163, 184, 0.3));
  box-shadow: var(--shadow-sm);
}

.btn--secondary:hover:not(:disabled) {
  background: var(--bg-primary, #f8fafc);
  border-color: var(--accent-cyan, #0891b2);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.btn--secondary:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: var(--shadow-sm);
}

/* Danger variant */
.btn--danger {
  background: linear-gradient(135deg, var(--color-danger, #ef4444), var(--color-danger-dark, #dc2626));
  color: white;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05), 0 0 0 1px rgba(255, 255, 255, 0.1) inset;
}

.btn--danger:hover:not(:disabled) {
  background: linear-gradient(135deg, var(--color-danger-dark, #dc2626), var(--color-danger-darker, #b91c1c));
  box-shadow: 0 4px 12px var(--color-danger-glow, rgba(239, 68, 68, 0.4)), 0 0 0 1px rgba(255, 255, 255, 0.15) inset;
  transform: translateY(-1px);
}

.btn--danger:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05), 0 0 0 1px rgba(255, 255, 255, 0.1) inset;
}

/* Disabled state */
.btn--disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}
</style>
