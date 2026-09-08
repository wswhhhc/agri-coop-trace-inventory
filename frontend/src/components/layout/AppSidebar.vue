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
  border-right: 1px solid var(--color-sidebar-border);
  background: var(--color-sidebar-bg);
  transition:
    background-color var(--duration-normal) var(--ease-standard),
    border-color var(--duration-normal) var(--ease-standard),
    transform var(--duration-normal) var(--ease-standard);
}

.app-sidebar__brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: 6rem;
  border-bottom: 1px solid var(--color-sidebar-border);
  padding: var(--space-5) var(--space-5) var(--space-4);
}

.app-sidebar__brand-mark {
  display: grid;
  width: 2.75rem;
  height: 2.75rem;
  flex: 0 0 2.75rem;
  place-items: center;
  border: 1px solid rgb(248 237 207 / 48%);
  border-radius: 0.85rem 0.85rem 0.85rem 0.25rem;
  background: var(--color-grain-500);
  color: var(--color-brand-950);
  font-family: var(--font-family-display);
  font-size: var(--font-size-xl);
  font-weight: 700;
  box-shadow: 0 6px 16px rgb(0 0 0 / 16%);
}

.app-sidebar__brand span:last-child {
  display: grid;
  gap: var(--space-1);
}

.app-sidebar__brand strong {
  color: var(--color-sidebar-text);
  font-size: var(--font-size-md);
}

.app-sidebar__brand small {
  color: var(--color-sidebar-muted);
  font-size: var(--font-size-xs);
}

.app-sidebar__nav {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-5) var(--space-3);
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
  border: 1px solid transparent;
  border-radius: 0.7rem;
  padding: var(--space-2) var(--space-3);
  color: var(--color-sidebar-muted);
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
  border-color: var(--color-sidebar-border);
  background: var(--color-sidebar-surface);
  color: var(--color-sidebar-text);
}

.app-sidebar__link.router-link-active::before,
.app-sidebar__link.router-link-exact-active::before {
  width: 0.3rem;
  height: 1.3rem;
  margin-right: var(--space-2);
  border-radius: var(--radius-pill);
  background: var(--color-grain-500);
  content: '';
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
