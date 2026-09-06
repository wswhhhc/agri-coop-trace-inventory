import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'

import * as authApi from '@/api/auth'
import { clearAccessToken, setAccessToken } from '@/api/session'
import { getApiErrorMessage } from '@/utils/api-error'
import type { CurrentUser } from '@/types/auth'

export type AuthStatus = 'unknown' | 'loading' | 'authenticated' | 'unauthenticated' | 'error'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<CurrentUser | null>(null)
  const permissions = ref<string[]>([])
  const status = ref<AuthStatus>('unknown')
  const errorMessage = ref('')
  const initialized = ref(false)
  let initializePromise: Promise<void> | null = null

  const isAuthenticated = computed(() => status.value === 'authenticated' && user.value !== null)
  const role = computed(() => user.value?.role ?? null)

  function clearUser(): void {
    clearAccessToken()
    user.value = null
    permissions.value = []
  }

  function isUnauthorized(error: unknown): boolean {
    if (axios.isAxiosError(error)) return error.response?.status === 401
    if (typeof error !== 'object' || error === null) return false
    const response = (error as { response?: { status?: number } }).response
    return response?.status === 401
  }

  async function login(username: string, password: string): Promise<void> {
    status.value = 'loading'
    errorMessage.value = ''

    try {
      const tokenData = await authApi.login({ username, password })
      setAccessToken(tokenData.accessToken)
      user.value = {
        ...tokenData.user,
        warehouseIds: null,
        permissions: tokenData.permissions,
      }
      permissions.value = tokenData.permissions
      status.value = 'authenticated'
      initialized.value = true
    } catch (error) {
      clearUser()
      status.value = 'unauthenticated'
      errorMessage.value = getApiErrorMessage(error, '登录失败，请检查用户名和密码')
      throw error
    }
  }

  async function initialize(): Promise<void> {
    if (initialized.value) return
    if (initializePromise) return initializePromise

    initializePromise = (async () => {
      status.value = 'loading'
      errorMessage.value = ''

      try {
        const tokenData = await authApi.refresh()
        setAccessToken(tokenData.accessToken)
        const currentUser = await authApi.getCurrentUser()
        user.value = currentUser
        permissions.value = currentUser.permissions
        status.value = 'authenticated'
      } catch (error) {
        clearUser()
        if (isUnauthorized(error)) {
          status.value = 'unauthenticated'
        } else {
          status.value = 'error'
          errorMessage.value = getApiErrorMessage(error, '系统初始化失败，请稍后重试')
        }
      } finally {
        initialized.value = true
        initializePromise = null
      }
    })()

    return initializePromise
  }

  async function logout(): Promise<void> {
    try {
      await authApi.logout()
    } finally {
      clearAccessToken()
      user.value = null
      permissions.value = []
      status.value = 'unauthenticated'
      initialized.value = true
    }
  }

  function hasPermission(permission: string): boolean {
    return permissions.value.includes(permission)
  }

  return {
    user,
    permissions,
    role,
    status,
    errorMessage,
    initialized,
    isAuthenticated,
    login,
    initialize,
    logout,
    hasPermission,
  }
})
