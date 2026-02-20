<script setup lang="ts">
import ShadcnTextarea from './shadcn/Textarea.vue'

defineOptions({ inheritAttrs: false })

interface Props {
  modelValue?: string
  label?: string
  placeholder?: string
  rows?: number
  error?: string
  disabled?: boolean
}

withDefaults(defineProps<Props>(), {
  modelValue: '',
  label: undefined,
  placeholder: undefined,
  rows: 4,
  error: undefined,
  disabled: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" class="text-sm font-medium text-foreground">{{ label }}</label>
    <ShadcnTextarea
      v-bind="$attrs"
      :model-value="modelValue"
      :placeholder="placeholder"
      :rows="rows"
      :disabled="disabled"
      :class="error ? 'border-destructive focus-visible:ring-destructive' : ''"
      @update:model-value="emit('update:modelValue', $event)"
    />
    <p v-if="error" class="text-xs text-destructive leading-snug">{{ error }}</p>
  </div>
</template>
