<script setup lang="ts">
import { useRoute } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()
</script>

<template>
  <dl class="page-context">
    <div class="page-context__item">
      <dt>当前路径</dt>
      <dd>{{ route.fullPath }}</dd>
    </div>
    <div class="page-context__item">
      <dt>当前用户</dt>
      <dd>{{ authStore.user?.displayName }}</dd>
    </div>
    <div class="page-context__item">
      <dt>当前角色</dt>
      <dd>{{ authStore.role }}</dd>
    </div>
  </dl>
</template>
