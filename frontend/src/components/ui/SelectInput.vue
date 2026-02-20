<script setup lang="ts">
defineOptions({ inheritAttrs: false })

interface Option {
  value: string | number
  label: string
}

interface Props {
  modelValue?: string | number
  label?: string
  options: Option[]
  placeholder?: string
  error?: string
  disabled?: boolean
}

withDefaults(defineProps<Props>(), {
  modelValue: '',
  label: undefined,
  placeholder: undefined,
  error: undefined,
  disabled: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string | number]
}>()

function handleChange(event: Event) {
  const target = event.target as HTMLSelectElement
  emit('update:modelValue', target.value)
}
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" class="text-sm font-medium text-foreground">{{ label }}</label>
    <div class="relative">
      <select
        v-bind="$attrs"
        :value="modelValue"
        :disabled="disabled"
        :class="[
          'flex h-10 w-full appearance-none rounded-md border bg-background px-3 py-2 pr-8 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 cursor-pointer',
          error ? 'border-destructive focus-visible:ring-destructive' : 'border-input'
        ]"
        @change="handleChange"
      >
        <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
        <option
          v-for="opt in options"
          :key="opt.value"
          :value="opt.value"
        >
          {{ opt.label }}
        </option>
      </select>
      <span class="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 flex items-center text-muted-foreground" aria-hidden="true">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path d="M3 4.5L6 7.5L9 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </span>
    </div>
    <p v-if="error" class="text-xs text-destructive leading-snug">{{ error }}</p>
  </div>
</template>
