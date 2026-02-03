<script setup lang="ts">
interface Props {
  modelValue?: string
  type?: 'text' | 'password' | 'email' | 'number' | 'search' | 'url'
  placeholder?: string
  label?: string
  error?: string
  disabled?: boolean
  required?: boolean
  autocomplete?: string
  id?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  type: 'text',
  placeholder: '',
  label: '',
  error: '',
  disabled: false,
  required: false,
  autocomplete: undefined,
  id: undefined,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  blur: [event: FocusEvent]
  focus: [event: FocusEvent]
  keydown: [event: KeyboardEvent]
}>()

const inputId = props.id || `input-${Math.random().toString(36).slice(2, 9)}`

function handleInput(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}

function handleBlur(event: FocusEvent) {
  emit('blur', event)
}

function handleFocus(event: FocusEvent) {
  emit('focus', event)
}

function handleKeydown(event: KeyboardEvent) {
  emit('keydown', event)
}
</script>

<template>
  <div class="input-wrapper">
    <label v-if="label" :for="inputId" class="input-label">
      {{ label }}
      <span v-if="required" class="input-required" aria-hidden="true">*</span>
    </label>
    <input
      :id="inputId"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :required="required"
      :autocomplete="autocomplete"
      :aria-invalid="!!error"
      :aria-describedby="error ? `${inputId}-error` : undefined"
      :class="['input', { 'input--error': error, 'input--disabled': disabled }]"
      @input="handleInput"
      @blur="handleBlur"
      @focus="handleFocus"
      @keydown="handleKeydown"
    />
    <p v-if="error" :id="`${inputId}-error`" class="input-error" role="alert">
      {{ error }}
    </p>
  </div>
</template>

<style scoped>
.input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  width: 100%;
}

.input-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary, rgba(255, 255, 255, 0.7));
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.input-required {
  color: var(--color-error, #ef4444);
}

.input {
  width: 100%;
  padding: 0.625rem 0.875rem;
  font-family: inherit;
  font-size: 0.9375rem;
  line-height: 1.5;
  color: var(--color-text-primary, rgba(255, 255, 255, 0.9));
  background: var(--color-surface, rgba(30, 30, 40, 0.6));
  border: 1px solid var(--color-border, rgba(255, 255, 255, 0.1));
  border-radius: 0.5rem;
  transition: all 0.2s ease;
  outline: none;
}

.input::placeholder {
  color: var(--color-text-muted, rgba(255, 255, 255, 0.4));
}

.input:hover:not(:disabled) {
  border-color: var(--color-border-hover, rgba(255, 255, 255, 0.2));
  background: var(--color-surface-hover, rgba(40, 40, 55, 0.7));
}

/* Focus ring using accent color */
.input:focus {
  border-color: var(--color-accent, #3b82f6);
  box-shadow:
    0 0 0 3px var(--color-accent-focus, rgba(59, 130, 246, 0.2)),
    0 0 0 1px var(--color-accent, #3b82f6) inset;
  background: var(--color-surface-elevated, rgba(40, 40, 55, 0.8));
}

/* Error state */
.input--error {
  border-color: var(--color-error, #ef4444);
  background: var(--color-error-bg, rgba(239, 68, 68, 0.1));
}

.input--error:focus {
  border-color: var(--color-error, #ef4444);
  box-shadow:
    0 0 0 3px var(--color-error-focus, rgba(239, 68, 68, 0.2)),
    0 0 0 1px var(--color-error, #ef4444) inset;
}

/* Disabled state */
.input--disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: var(--color-surface-muted, rgba(30, 30, 40, 0.4));
}

.input--disabled:hover {
  border-color: var(--color-border, rgba(255, 255, 255, 0.1));
}

.input-error {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--color-error, #ef4444);
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.input-error::before {
  content: '';
  display: inline-block;
  width: 0.875rem;
  height: 0.875rem;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23ef4444' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3Cline x1='12' y1='8' x2='12' y2='12'/%3E%3Cline x1='12' y1='16' x2='12.01' y2='16'/%3E%3C/svg%3E");
  background-size: contain;
  background-repeat: no-repeat;
  flex-shrink: 0;
}
</style>
