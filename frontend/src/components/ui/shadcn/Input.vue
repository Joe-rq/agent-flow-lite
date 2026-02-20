<script setup lang="ts">
import { type HTMLAttributes, computed } from 'vue'
import { cn } from '@/lib/utils'

interface Props {
  class?: HTMLAttributes['class']
  defaultValue?: string | number
  modelValue?: string | number
}

const props = withDefaults(defineProps<Props>(), {
  class: undefined,
  defaultValue: undefined,
  modelValue: undefined,
})

const emits = defineEmits<{
  'update:modelValue': [value: string]
}>()

const modelValue = computed({
  get: () => props.modelValue,
  set: (val) => emits('update:modelValue', String(val ?? '')),
})
</script>

<template>
  <input
    v-model="modelValue"
    :class="cn('flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50', props.class)"
    :default-value="defaultValue"
  />
</template>
