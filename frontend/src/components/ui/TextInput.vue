<script setup lang="ts">
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

function handleInput(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}
</script>

<template>
  <div :class="['text-input', { 'text-input--error': error, 'text-input--disabled': disabled }]">
    <label v-if="label" class="text-input__label">
      {{ label }}
      <span v-if="required" class="text-input__required">*</span>
    </label>
    <input
      v-bind="$attrs"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :required="required"
      class="text-input__field"
      @input="handleInput"
    />
    <p v-if="error" class="text-input__error">{{ error }}</p>
  </div>
</template>

<style scoped src="./TextInput.css"></style>
