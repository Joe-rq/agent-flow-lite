<script setup lang="ts">
import ShadcnInput from './shadcn/Input.vue'

defineOptions({ inheritAttrs: false })

interface Props {
  modelValue?: string | number
  label?: string
  placeholder?: string
  type?: 'text' | 'email' | 'password' | 'number'
  error?: string
  disabled?: boolean
  required?: boolean
}

withDefaults(defineProps<Props>(), {
  modelValue: '',
  label: undefined,
  placeholder: undefined,
  type: 'text',
  error: undefined,
  disabled: false,
  required: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" class="text-sm font-medium text-foreground">
      {{ label }}
      <span v-if="required" class="text-destructive ml-0.5">*</span>
    </label>
    <ShadcnInput
      v-bind="$attrs"
      :type="type"
      :model-value="String(modelValue)"
      :placeholder="placeholder"
      :disabled="disabled"
      :required="required"
      :class="error ? 'border-destructive focus-visible:ring-destructive' : ''"
      @update:model-value="emit('update:modelValue', $event)"
    />
    <p v-if="error" class="text-xs text-destructive leading-snug">{{ error }}</p>
  </div>
</template>
