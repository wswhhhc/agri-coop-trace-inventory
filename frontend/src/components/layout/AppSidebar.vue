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
