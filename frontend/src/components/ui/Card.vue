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
  background: var(--color-surface, rgba(30, 30, 40, 0.6));
  border: 1px solid var(--color-border, rgba(255, 255, 255, 0.08));
  border-radius: 1rem;
  overflow: hidden;
  transition: all 0.3s ease;
}

/* Glassmorphism effect with fallback */
.card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.1) 0%,
    rgba(255, 255, 255, 0.02) 50%,
    rgba(255, 255, 255, 0) 100%
  );
  pointer-events: none;
  border-radius: inherit;
}

/* Backdrop filter with webkit prefix and fallback */
@supports (backdrop-filter: blur(20px)) or (-webkit-backdrop-filter: blur(20px)) {
  .card {
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    background: var(--color-surface-glass, rgba(30, 30, 40, 0.4));
  }
}

/* Fallback for browsers without backdrop-filter support */
@supports not ((backdrop-filter: blur(20px)) or (-webkit-backdrop-filter: blur(20px))) {
  .card {
    background: var(--color-surface-solid, rgba(40, 40, 55, 0.95));
  }
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
  border-color: var(--color-border-hover, rgba(255, 255, 255, 0.15));
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.3),
    0 0 0 1px rgba(255, 255, 255, 0.05) inset;
  transform: translateY(-2px);
}

/* Subtle inner glow */
.card::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.2),
    transparent
  );
  pointer-events: none;
}
</style>
