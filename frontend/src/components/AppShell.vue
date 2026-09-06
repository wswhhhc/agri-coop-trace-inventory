<script setup lang="ts">
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

async function handleLogout(): Promise<void> {
  await authStore.logout()
  await router.replace({ name: 'login' })
}
</script>

<template>
  <div class="app-shell">
    <header class="app-shell__header">
      <div>
        <p>农业合作社追溯与库存系统</p>
        <span>当前登录：{{ authStore.user?.displayName }}</span>
      </div>
      <button type="button" @click="handleLogout">退出登录</button>
    </header>

    <main class="app-shell__content">
      <slot />
    </main>
  </div>
</template>
