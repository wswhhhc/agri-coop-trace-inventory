<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

import { filterMenuItems, menuItems } from '@/router/menu'

defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const authStore = useAuthStore()

const visibleMenuItems = computed(() => {
  if (!authStore.role) return []
  return filterMenuItems(menuItems, {
    role: authStore.role,
    permissions: authStore.permissions,
  })
})
</script>

<template>
  <aside class="app-sidebar" :class="{ 'app-sidebar--open': open }" aria-label="后台导航">
    <div class="app-sidebar__brand">
      <span class="app-sidebar__brand-mark" aria-hidden="true">农</span>
      <span>
        <strong>农业合作社</strong>
        <small>数字化运营平台</small>
      </span>
    </div>
    <nav class="app-sidebar__nav">
      <ul class="app-sidebar__menu">
        <li v-for="item in visibleMenuItems" :key="item.path" class="app-sidebar__menu-item">
          <RouterLink class="app-sidebar__link" :to="item.path" @click="emit('close')">
            {{ item.title }}
          </RouterLink>
          <ul v-if="item.children?.length" class="app-sidebar__submenu">
            <li v-for="child in item.children" :key="child.path" class="app-sidebar__submenu-item">
              <RouterLink class="app-sidebar__link" :to="child.path" @click="emit('close')">
                {{ child.title }}
              </RouterLink>
            </li>
          </ul>
        </li>
      </ul>
    </nav>
  </aside>
</template>

<style scoped>
.app-sidebar {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  flex: 0 0 16rem;
  flex-direction: column;
  width: 16rem;
  height: 100dvh;
  border-right: 1px solid var(--color-border);
  background: var(--color-surface);
  transition:
    background-color var(--duration-normal) var(--ease-standard),
    border-color var(--duration-normal) var(--ease-standard),
    transform var(--duration-normal) var(--ease-standard);
}

.app-sidebar__brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: 5rem;
  border-bottom: 1px solid var(--color-border);
  padding: var(--space-5);
}

.app-sidebar__brand-mark {
  display: grid;
  width: 2.5rem;
  height: 2.5rem;
  flex: 0 0 2.5rem;
  place-items: center;
  border-radius: var(--radius-md);
  background: var(--color-brand);
  color: var(--color-text-on-brand);
  font-size: var(--font-size-lg);
  font-weight: 700;
}

.app-sidebar__brand span:last-child {
  display: grid;
  gap: var(--space-1);
}

.app-sidebar__brand strong {
  color: var(--color-text);
  font-size: var(--font-size-md);
}

.app-sidebar__brand small {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.app-sidebar__nav {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-4) var(--space-3);
}

.app-sidebar__menu,
.app-sidebar__submenu {
  display: grid;
  gap: var(--space-1);
  margin: 0;
  padding: 0;
  list-style: none;
}

.app-sidebar__submenu {
  margin: var(--space-1) 0 var(--space-2) var(--space-4);
}

.app-sidebar__link {
  display: flex;
  min-height: 2.75rem;
  align-items: center;
  border-radius: var(--radius-md);
  padding: var(--space-2) var(--space-3);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 600;
  text-decoration: none;
  transition:
    background-color var(--duration-fast) var(--ease-standard),
    color var(--duration-fast) var(--ease-standard);
}

.app-sidebar__link:hover,
.app-sidebar__link.router-link-active,
.app-sidebar__link.router-link-exact-active {
  background: var(--color-brand-soft);
  color: var(--color-brand);
}

@media (max-width: 48rem) {
  .app-sidebar {
    position: fixed;
    left: 0;
    transform: translateX(-100%);
  }

  .app-sidebar--open {
    transform: translateX(0);
    box-shadow: var(--shadow-md);
  }
}
</style>
