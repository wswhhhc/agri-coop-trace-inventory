<script setup lang="ts">
import AppShell from '@/components/AppShell.vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
</script>

<template>
  <AppShell>
    <section class="home-page" aria-labelledby="home-title">
      <h1 id="home-title">系统首页</h1>
      <p>登录已成功，后续业务页面将在这里逐步接入。</p>

      <dl>
        <div>
          <dt>用户名</dt>
          <dd>{{ authStore.user?.username }}</dd>
        </div>
        <div>
          <dt>角色</dt>
          <dd>{{ authStore.user?.role }}</dd>
        </div>
        <div>
          <dt>合作社</dt>
          <dd>{{ authStore.user?.cooperativeId ?? '平台级账号' }}</dd>
        </div>
      </dl>

      <section aria-labelledby="permission-title">
        <h2 id="permission-title">当前权限</h2>
        <ul>
          <li v-for="permission in authStore.permissions" :key="permission">
            {{ permission }}
          </li>
          <li v-if="authStore.permissions.length === 0">暂无权限数据</li>
        </ul>
      </section>
    </section>
  </AppShell>
</template>
