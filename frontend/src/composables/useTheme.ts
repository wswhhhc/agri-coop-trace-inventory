import { onBeforeUnmount, onMounted, ref } from 'vue'

export type ThemePreference = 'light' | 'dark' | 'system'
export type ResolvedTheme = 'light' | 'dark'

export const DEFAULT_THEME: ThemePreference = 'system'
export const THEME_STORAGE_KEY = 'agri-ui-theme'

const THEME_VALUES: ThemePreference[] = ['light', 'dark', 'system']

function getStorage(): Storage | undefined {
  try {
    return window.localStorage
  } catch {
    return undefined
  }
}

export function isThemePreference(value: string | null): value is ThemePreference {
  return value !== null && THEME_VALUES.includes(value as ThemePreference)
}

export function readThemePreference(storage: Storage | undefined = getStorage()): ThemePreference {
  const value = storage?.getItem(THEME_STORAGE_KEY) ?? null
  return isThemePreference(value) ? value : DEFAULT_THEME
}

export function applyTheme(
  preference: ThemePreference,
  root: HTMLElement = document.documentElement,
): void {
  root.dataset.theme = preference
}

export function setThemePreference(
  preference: ThemePreference,
  storage: Storage | undefined = getStorage(),
  root: HTMLElement = document.documentElement,
): void {
  storage?.setItem(THEME_STORAGE_KEY, preference)
  applyTheme(preference, root)
}

export function initializeTheme(
  storage: Storage | undefined = getStorage(),
  root: HTMLElement = document.documentElement,
): ThemePreference {
  const preference = readThemePreference(storage)
  applyTheme(preference, root)
  return preference
}

export function resolveTheme(preference: ThemePreference, systemIsDark: boolean): ResolvedTheme {
  if (preference === 'system') return systemIsDark ? 'dark' : 'light'
  return preference
}

export function useTheme() {
  const preference = ref<ThemePreference>(initializeTheme())
  const resolvedTheme = ref<ResolvedTheme>(resolveTheme(preference.value, false))
  let mediaQuery: MediaQueryList | null = null

  function syncResolvedTheme(): void {
    resolvedTheme.value = resolveTheme(preference.value, mediaQuery?.matches ?? false)
  }

  function setTheme(nextTheme: ThemePreference): void {
    preference.value = nextTheme
    setThemePreference(nextTheme)
    syncResolvedTheme()
  }

  function handleSystemThemeChange(): void {
    syncResolvedTheme()
  }

  onMounted(() => {
    mediaQuery = window.matchMedia?.('(prefers-color-scheme: dark)') ?? null
    mediaQuery?.addEventListener('change', handleSystemThemeChange)
    syncResolvedTheme()
  })

  onBeforeUnmount(() => {
    mediaQuery?.removeEventListener('change', handleSystemThemeChange)
  })

  return { preference, resolvedTheme, setTheme }
}
