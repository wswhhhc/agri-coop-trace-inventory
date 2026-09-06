<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const isSubmitting = ref(false)

const form = reactive({
  username: '',
  password: '',
})

async function handleSubmit(): Promise<void> {
  if (!form.username.trim() || !form.password) {
    authStore.errorMessage = '请输入用户名和密码'
    return
  }

  isSubmitting.value = true
  try {
    await authStore.login(form.username.trim(), form.password)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    await router.replace(redirect)
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <main class="login-page">
    <section class="login-panel" aria-labelledby="login-title">
      <h1 id="login-title">登录系统</h1>
      <p>请输入后台账号继续</p>

      <form novalidate @submit.prevent="handleSubmit">
        <div>
          <label for="username">用户名</label>
          <input
            id="username"
            v-model="form.username"
            name="username"
            autocomplete="username"
            required
          />
        </div>

        <div>
          <label for="password">密码</label>
          <input
            id="password"
            v-model="form.password"
            name="password"
            type="password"
            autocomplete="current-password"
            required
          />
        </div>

        <p v-if="authStore.errorMessage" role="alert">{{ authStore.errorMessage }}</p>

        <button type="submit" :disabled="isSubmitting">
          {{ isSubmitting ? '登录中…' : '登录' }}
        </button>
      </form>
    </section>
  </main>
</template>
