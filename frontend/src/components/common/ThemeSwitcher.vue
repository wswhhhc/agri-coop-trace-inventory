<script setup lang="ts">
import { useTheme, type ThemePreference } from '@/composables/useTheme'

const { preference, resolvedTheme, setTheme } = useTheme()

function handleChange(event: Event): void {
  const value = (event.target as HTMLSelectElement).value as ThemePreference
  setTheme(value)
}
</script>

<template>
  <label class="theme-switcher">
    <span>主题</span>
    <select
      :value="preference"
      aria-label="选择主题模式"
      @change="handleChange"
    >
      <option value="system">自动（{{ resolvedTheme === 'dark' ? '深色' : '浅色' }}）</option>
      <option value="light">浅色</option>
      <option value="dark">深色</option>
    </select>
  </label>
</template>

<style scoped>
.theme-switcher {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  white-space: nowrap;
}

.theme-switcher select {
  min-height: 2.5rem;
  padding-block: var(--space-1);
}

@media (max-width: 48rem) {
  .theme-switcher > span {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0 0 0 0);
    white-space: nowrap;
  }
}
</style>
