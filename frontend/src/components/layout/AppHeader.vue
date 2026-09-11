<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { changePassword } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { getApiErrorMessage } from '@/utils/api-error'
import ModalShell from '@/components/common/ModalShell.vue'
import ThemeSwitcher from '@/components/common/ThemeSwitcher.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const showChangePassword = ref(false)
const changingPassword = ref(false)
const changePasswordError = ref('')
const changePasswordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

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

function resetChangePasswordForm(): void {
  changePasswordForm.currentPassword = ''
  changePasswordForm.newPassword = ''
  changePasswordForm.confirmPassword = ''
  changePasswordError.value = ''
}

function openChangePassword(): void {
  resetChangePasswordForm()
  showChangePassword.value = true
}

function closeChangePassword(): void {
  if (changingPassword.value) return
  showChangePassword.value = false
  changePasswordError.value = ''
}

async function handleChangePassword(): Promise<void> {
  if (changePasswordForm.newPassword !== changePasswordForm.confirmPassword) {
    changePasswordError.value = '两次输入的新密码不一致。'
    return
  }
  changingPassword.value = true
  changePasswordError.value = ''
  try {
    await changePassword({
      currentPassword: changePasswordForm.currentPassword,
      newPassword: changePasswordForm.newPassword,
    })
  } catch (reason) {
    changePasswordError.value = getApiErrorMessage(reason)
    return
  } finally {
    changingPassword.value = false
  }

  showChangePassword.value = false
  await authStore.logout().catch(() => undefined)
  await router.replace({ name: 'login' })
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
      <button class="app-header__change-password" type="button" @click="openChangePassword">修改密码</button>
      <button class="app-header__logout" type="button" @click="handleLogout">退出登录</button>
    </div>

    <ModalShell :open="showChangePassword" title="修改密码" @close="closeChangePassword">
      <form class="change-password-form" @submit.prevent="handleChangePassword">
        <p class="change-password-form__hint">修改成功后需要重新登录。</p>
        <label>
          当前密码
          <input
            v-model="changePasswordForm.currentPassword"
            type="password"
            name="currentPassword"
            autocomplete="current-password"
            required
            maxlength="128"
          />
        </label>
        <label>
          新密码
          <input
            v-model="changePasswordForm.newPassword"
            type="password"
            name="newPassword"
            autocomplete="new-password"
            required
            minlength="8"
            maxlength="128"
          />
        </label>
        <label>
          确认新密码
          <input
            v-model="changePasswordForm.confirmPassword"
            type="password"
            name="confirmPassword"
            autocomplete="new-password"
            required
            minlength="8"
            maxlength="128"
          />
        </label>
        <p v-if="changePasswordError" class="change-password-form__error" role="alert">
          {{ changePasswordError }}
        </p>
        <div class="change-password-form__actions">
          <button type="button" class="change-password-form__cancel" :disabled="changingPassword" @click="closeChangePassword">
            取消
          </button>
          <button type="submit" :disabled="changingPassword">
            {{ changingPassword ? '提交中…' : '确认修改' }}
          </button>
        </div>
      </form>
    </ModalShell>
  </header>
</template>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  min-height: 5rem;
  align-items: center;
  gap: var(--space-4);
  border-bottom: 1px solid color-mix(in srgb, var(--color-border) 84%, var(--color-brand));
  padding: var(--space-3) clamp(1.25rem, 4vw, 4rem);
  background: color-mix(in srgb, var(--color-surface) 88%, transparent);
  backdrop-filter: blur(12px);
}

.app-header::before {
  position: absolute;
  top: 0;
  right: 0;
  left: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--color-brand), var(--color-grain-500), transparent 72%);
  content: '';
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
  color: var(--color-brand);
  font-weight: 650;
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
  padding-left: var(--space-4);
  border-left: 1px solid var(--color-border);
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

.app-header__change-password,
.app-header__logout {
  border-color: var(--color-border-strong);
  background: transparent;
  color: var(--color-text-secondary);
}

.app-header__change-password:hover:not(:disabled),
.app-header__logout:hover:not(:disabled) {
  background: var(--color-surface-muted);
  color: var(--color-brand);
}

.change-password-form {
  display: grid;
  gap: var(--space-4);
}

.change-password-form__hint {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.change-password-form label {
  display: grid;
  gap: var(--space-1);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.change-password-form__error {
  margin: 0;
  color: var(--color-danger);
  font-size: var(--font-size-sm);
}

.change-password-form__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}

.change-password-form__cancel {
  border-color: var(--color-border-strong);
  background: transparent;
  color: var(--color-text-secondary);
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
