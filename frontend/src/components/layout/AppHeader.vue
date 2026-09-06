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
