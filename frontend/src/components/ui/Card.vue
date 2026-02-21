<script setup lang="ts">
import { cn } from '@/lib/utils'
import { type HTMLAttributes } from 'vue'

interface Props {
  padding?: 'none' | 'sm' | 'md' | 'lg'
  hover?: boolean
  class?: HTMLAttributes['class']
}

const props = withDefaults(defineProps<Props>(), {
  padding: 'md',
  hover: true,
  class: undefined,
})

const paddingMap = {
  none: 'p-0',
  sm: 'p-3',
  md: 'p-5',
  lg: 'p-8',
} as const
</script>

<template>
  <div
    :class="cn(
      'rounded-xl border border-border bg-card shadow-sm transition-all duration-300',
      paddingMap[props.padding],
      props.hover && 'hover:border-primary/30 hover:shadow-md',
      props.class
    )"
  >
    <slot />
  </div>
</template>
