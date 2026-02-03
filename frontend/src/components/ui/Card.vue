<script setup lang="ts">
interface Props {
  padding?: 'none' | 'sm' | 'md' | 'lg'
  hover?: boolean
}

withDefaults(defineProps<Props>(), {
  padding: 'md',
  hover: true,
})
</script>

<template>
  <div :class="['card', `card--padding-${padding}`, { 'card--hover': hover }]">
    <slot />
  </div>
</template>

<style scoped>
.card {
  position: relative;
  background: var(--bg-secondary, #ffffff);
  border: 1px solid var(--border-primary, rgba(148, 163, 184, 0.3));
  border-radius: var(--radius-lg, 12px);
  overflow: hidden;
  transition: all 0.3s ease;
  box-shadow: var(--shadow-sm, 0 1px 2px rgba(15, 23, 42, 0.05));
}

/* Padding variants */
.card--padding-none {
  padding: 0;
}

.card--padding-sm {
  padding: 0.75rem;
}

.card--padding-md {
  padding: 1.25rem;
}

.card--padding-lg {
  padding: 2rem;
}

/* Hover effect */
.card--hover:hover {
  border-color: var(--accent-cyan, #0891b2);
  box-shadow: var(--shadow-md, 0 4px 6px rgba(15, 23, 42, 0.07));
  transform: translateY(-2px);
}
</style>
