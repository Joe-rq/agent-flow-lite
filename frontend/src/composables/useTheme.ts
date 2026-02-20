import { ref, watch } from 'vue'

type Theme = 'light' | 'dark' | 'system'

const theme = ref<Theme>((localStorage.getItem('theme') as Theme) || 'system')

function getSystemTheme(): 'light' | 'dark' {
  if (typeof window !== 'undefined' && window.matchMedia) {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }
  return 'light'
}

function applyTheme(t: Theme) {
  const resolved = t === 'system' ? getSystemTheme() : t
  document.documentElement.classList.toggle('dark', resolved === 'dark')
}

// Apply on load
applyTheme(theme.value)

// Listen for system theme changes
if (typeof window !== 'undefined' && window.matchMedia) {
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (theme.value === 'system') {
      applyTheme('system')
    }
  })
}

watch(theme, (newTheme) => {
  localStorage.setItem('theme', newTheme)
  applyTheme(newTheme)
})

export function useTheme() {
  function setTheme(t: Theme) {
    theme.value = t
  }

  function toggleTheme() {
    const resolved = theme.value === 'system' ? getSystemTheme() : theme.value
    theme.value = resolved === 'light' ? 'dark' : 'light'
  }

  return {
    theme,
    setTheme,
    toggleTheme,
  }
}
