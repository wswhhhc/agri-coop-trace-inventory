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
  } catch {
    // authStore 已将后端错误转换为页面可展示的 errorMessage。
    // 这里消费异常，避免浏览器控制台出现 Unhandled Promise Rejection。
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <main class="login-page">
    <aside class="login-visual" aria-label="平台简介">
      <div class="login-visual__brand">
        <span class="login-visual__mark" aria-hidden="true">农</span>
        <span>农业合作社</span>
      </div>
      <div class="login-visual__message">
        <p class="login-visual__eyebrow">从田间到仓库</p>
        <h2>让每一批<br />都有迹可循。</h2>
        <p>批次、库存、预警和流转记录，在一个清晰的运营台里协同起来。</p>
      </div>
      <div class="login-visual__route" aria-hidden="true">
        <span>采收</span><i></i><span>质检</span><i></i><span>入库</span><i></i><span>交付</span>
      </div>
    </aside>
    <section class="login-panel" aria-labelledby="login-title">
      <div class="login-panel__heading">
        <p class="login-panel__eyebrow">运营台入口</p>
        <span class="login-panel__status"><i></i>系统运行中</span>
      </div>
      <h1 id="login-title">登录系统</h1>
      <p class="login-panel__intro">请输入后台账号，继续管理合作社业务。</p>

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

<style scoped>
.login-page {
  display: grid;
  grid-template-columns: minmax(18rem, 0.9fr) minmax(24rem, 1.1fr);
  gap: clamp(2rem, 8vw, 8rem);
  align-items: stretch;
  min-height: 100dvh;
  padding: clamp(1.5rem, 5vw, 5rem) clamp(1.5rem, 9vw, 10rem);
  background:
    linear-gradient(125deg, var(--color-brand-950) 0 40%, transparent 40%),
    radial-gradient(circle at 78% 10%, var(--color-accent-soft), transparent 23rem),
    var(--color-bg);
}

.login-visual {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 34rem;
  color: var(--color-sidebar-text);
}

.login-visual__brand,
.login-visual__route {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-weight: 700;
}

.login-visual__mark {
  display: grid;
  width: 2.75rem;
  height: 2.75rem;
  place-items: center;
  border: 1px solid rgb(248 237 207 / 48%);
  border-radius: 0.85rem 0.85rem 0.85rem 0.25rem;
  background: var(--color-grain-500);
  color: var(--color-brand-950);
  font-family: var(--font-family-display);
  font-size: var(--font-size-xl);
}

.login-visual__message {
  max-width: 28rem;
  margin-block: auto;
  padding-block: 6rem 4rem;
}

.login-visual__eyebrow,
.login-panel__eyebrow {
  margin-bottom: var(--space-4);
  color: var(--color-grain-500);
  font-size: var(--font-size-sm);
  font-weight: 700;
}

.login-visual__message h2 {
  margin-bottom: var(--space-5);
  color: inherit;
  font-family: var(--font-family-display);
  font-size: clamp(2.8rem, 5vw, 4.8rem);
  font-weight: 600;
  letter-spacing: -0.06em;
  line-height: 1.08;
}

.login-visual__message > p:last-child {
  max-width: 24rem;
  margin: 0;
  color: var(--color-sidebar-muted);
  line-height: var(--line-height-relaxed);
}

.login-visual__route {
  color: var(--color-sidebar-muted);
  font-size: var(--font-size-xs);
  font-weight: 600;
}

.login-visual__route i {
  display: block;
  width: 2.5rem;
  height: 1px;
  background: var(--color-sidebar-border);
}

.login-panel {
  align-self: center;
  width: min(100%, 28rem);
  justify-self: end;
  border: 1px solid var(--color-border);
  border-radius: 1.25rem;
  padding: clamp(1.5rem, 4vw, 2.75rem);
  background: color-mix(in srgb, var(--color-surface) 93%, transparent);
  box-shadow: var(--shadow-lg);
}

.login-panel__heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.login-panel__eyebrow {
  margin-bottom: 0;
  color: var(--color-brand);
}

.login-panel__status {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-success);
  font-size: var(--font-size-xs);
  font-weight: 600;
}

.login-panel__status i {
  width: 0.45rem;
  height: 0.45rem;
  border-radius: var(--radius-pill);
  background: currentColor;
  box-shadow: 0 0 0 4px var(--color-success-soft);
}

.login-panel h1 {
  margin: var(--space-8) 0 var(--space-2);
  font-family: var(--font-family-display);
  font-size: clamp(2rem, 4vw, 2.75rem);
  font-weight: 600;
  letter-spacing: -0.04em;
}

.login-panel__intro {
  margin-bottom: var(--space-8);
  color: var(--color-text-muted);
}

.login-panel form,
.login-panel form > div {
  display: grid;
  gap: var(--space-3);
}

.login-panel form {
  gap: var(--space-5);
}

.login-panel label {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 650;
}

.login-panel input {
  min-height: 3rem;
  margin-top: var(--space-1);
  background: color-mix(in srgb, var(--color-surface) 92%, var(--color-brand-soft));
}

.login-panel button {
  min-height: 3rem;
  margin-top: var(--space-2);
  box-shadow: 0 8px 16px rgb(23 107 77 / 20%);
}

@media (max-width: 48rem) {
  .login-page {
    display: block;
    padding: 1rem;
    background: var(--color-bg);
  }

  .login-visual {
    display: none;
  }

  .login-panel {
    width: min(100%, 30rem);
    margin: 8vh auto 0;
  }
}
</style>
