<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import ThemeSwitcher from '@/components/common/ThemeSwitcher.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const emit = defineEmits<{
  toggleSidebar: []
}>()

async function handleLogout(): Promise<void> {
  try {
    await authStore.logout()
  } catch {
    // 即使退出接口异常，也清理本地认证状态并离开后台。
  } finally {
    await router.replace({ name: 'login' })
  }
}
</script>

<template>
  <header class="app-header">
    <button
      class="app-header__menu-button"
      type="button"
      aria-label="打开导航"
      @click="emit('toggleSidebar')"
    >
      <span class="app-header__menu-icon" aria-hidden="true">
        <span />
        <span />
        <span />
      </span>
    </button>
    <div class="app-header__context">
      <span>农业数字化运营平台</span>
      <strong>{{ route.meta.title }}</strong>
    </div>
    <div class="app-header__user" aria-label="当前用户信息">
      <span class="app-header__display-name">{{ authStore.user?.displayName }}</span>
      <span class="app-header__role">{{ authStore.role }}</span>
    </div>
    <div class="app-header__actions">
      <ThemeSwitcher />
      <button class="app-header__logout" type="button" @click="handleLogout">退出登录</button>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  min-height: 4.5rem;
  align-items: center;
  gap: var(--space-4);
  border-bottom: 1px solid var(--color-border);
  padding: var(--space-3) var(--space-8);
  background: color-mix(in srgb, var(--color-surface) 94%, transparent);
  backdrop-filter: blur(12px);
}

.app-header__menu-button {
  display: none;
  min-width: 2.75rem;
  padding: var(--space-2);
  background: transparent;
  color: var(--color-text-secondary);
}

.app-header__menu-button:hover:not(:disabled) {
  background: var(--color-surface-muted);
  color: var(--color-brand);
}

.app-header__menu-icon {
  display: grid;
  gap: 0.25rem;
  width: 1.25rem;
}

.app-header__menu-icon span {
  display: block;
  height: 2px;
  border-radius: var(--radius-pill);
  background: currentColor;
}

.app-header__context {
  display: grid;
  gap: var(--space-1);
  min-width: 0;
  margin-right: auto;
}

.app-header__context span {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.app-header__context strong {
  overflow: hidden;
  color: var(--color-text);
  font-size: var(--font-size-lg);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.app-header__user {
  display: grid;
  gap: var(--space-1);
  text-align: right;
}

.app-header__display-name {
  color: var(--color-text);
  font-size: var(--font-size-sm);
  font-weight: 700;
}

.app-header__role {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.app-header__actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.app-header__logout {
  border-color: var(--color-border-strong);
  background: transparent;
  color: var(--color-text-secondary);
}

.app-header__logout:hover:not(:disabled) {
  background: var(--color-surface-muted);
  color: var(--color-brand);
}

@media (max-width: 64rem) {
  .app-header {
    padding-inline: var(--space-5);
  }
}

@media (max-width: 48rem) {
  .app-header {
    min-height: 4rem;
    padding-block: var(--space-2);
  }

  .app-header__menu-button {
    display: inline-grid;
    place-items: center;
  }

  .app-header__user {
    display: none;
  }

  .app-header__actions {
    gap: var(--space-2);
  }
}
</style>
