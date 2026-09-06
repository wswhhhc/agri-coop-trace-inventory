import { beforeEach, describe, expect, it } from 'vitest'

import {
  applyTheme,
  DEFAULT_THEME,
  initializeTheme,
  readThemePreference,
  resolveTheme,
  setThemePreference,
  THEME_STORAGE_KEY,
  type ThemePreference,
} from './useTheme'

describe('theme preference', () => {
  let storage: Storage

  beforeEach(() => {
    const values = new Map<string, string>()
    storage = {
      getItem: (key) => values.get(key) ?? null,
      setItem: (key, value) => values.set(key, value),
      removeItem: (key) => values.delete(key),
      clear: () => values.clear(),
      key: (index) => Array.from(values.keys())[index] ?? null,
      get length() {
        return values.size
      },
    }
    document.documentElement.removeAttribute('data-theme')
  })

  it('uses system mode by default and ignores invalid stored values', () => {
    expect(readThemePreference(storage)).toBe(DEFAULT_THEME)

    storage.setItem(THEME_STORAGE_KEY, 'invalid')
    expect(readThemePreference(storage)).toBe(DEFAULT_THEME)
  })

  it.each<ThemePreference>(['light', 'dark', 'system'])('applies %s to the document root', (theme) => {
    applyTheme(theme)

    expect(document.documentElement.dataset.theme).toBe(theme)
  })

  it('restores a valid stored preference', () => {
    storage.setItem(THEME_STORAGE_KEY, 'dark')

    expect(readThemePreference(storage)).toBe('dark')
  })

  it('persists and applies a manually selected preference', () => {
    setThemePreference('light', storage)

    expect(storage.getItem(THEME_STORAGE_KEY)).toBe('light')
    expect(document.documentElement.dataset.theme).toBe('light')
  })

  it('initializes from storage and resolves system mode', () => {
    storage.setItem(THEME_STORAGE_KEY, 'system')

    expect(initializeTheme(storage)).toBe('system')
    expect(resolveTheme('system', true)).toBe('dark')
    expect(resolveTheme('system', false)).toBe('light')
  })
})
