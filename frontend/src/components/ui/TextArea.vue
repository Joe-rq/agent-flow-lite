<script setup lang="ts">
interface Props {
  modelValue: string
  label?: string
  placeholder?: string
  rows?: number
  error?: string
  disabled?: boolean
}

withDefaults(defineProps<Props>(), {
  label: undefined,
  placeholder: undefined,
  rows: 4,
  error: undefined,
  disabled: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

function handleInput(event: Event) {
  const target = event.target as HTMLTextAreaElement
  emit('update:modelValue', target.value)
}
</script>

<template>
  <div :class="['text-area', { 'text-area--error': error, 'text-area--disabled': disabled }]">
    <label v-if="label" class="text-area__label">{{ label }}</label>
    <textarea
      :value="modelValue"
      :placeholder="placeholder"
      :rows="rows"
      :disabled="disabled"
      class="text-area__field"
      @input="handleInput"
    />
    <p v-if="error" class="text-area__error">{{ error }}</p>
  </div>
</template>

<style scoped src="./TextArea.css"></style>
