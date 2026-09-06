import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { getCurrentUser, login as loginApi, refresh } from '@/api/auth'
import { clearAccessToken, getAccessToken } from '@/api/session'
import { useAuthStore } from './auth'

vi.mock('@/api/auth', () => ({
  login: vi.fn(),
  refresh: vi.fn(),
  getCurrentUser: vi.fn(),
  logout: vi.fn(),
}))

describe('auth store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    clearAccessToken()
    vi.clearAllMocks()
  })

  it('stores the access token, user and permissions after login', async () => {
    vi.mocked(loginApi).mockResolvedValue({
      accessToken: 'access-token',
      tokenType: 'Bearer',
      expiresIn: 1800,
      user: {
        id: 'user-1',
        username: 'coop_admin',
        displayName: '合作社管理员',
        role: 'COOPERATIVE_ADMIN',
        cooperativeId: 'coop-1',
        status: 'ACTIVE',
      },
      permissions: ['inventory:read'],
    })

    const store = useAuthStore()
    await store.login('coop_admin', 'password')

    expect(getAccessToken()).toBe('access-token')
    expect(store.isAuthenticated).toBe(true)
    expect(store.user?.displayName).toBe('合作社管理员')
    expect(store.permissions).toEqual(['inventory:read'])
  })

  it('refreshes before loading the current user and stays quietly unauthenticated on refresh 401', async () => {
    vi.mocked(refresh).mockRejectedValue({ response: { status: 401 } })

    const store = useAuthStore()
    await store.initialize()

    expect(refresh).toHaveBeenCalledOnce()
    expect(getCurrentUser).not.toHaveBeenCalled()
    expect(store.isAuthenticated).toBe(false)
    expect(store.errorMessage).toBe('')
    expect(store.initialized).toBe(true)
  })

  it('restores the authenticated user once after a successful refresh', async () => {
    vi.mocked(refresh).mockResolvedValue({
      accessToken: 'refreshed-token',
      tokenType: 'Bearer',
      expiresIn: 1800,
      user: {
        id: 'user-1',
        username: 'coop_admin',
        displayName: '合作社管理员',
        role: 'COOPERATIVE_ADMIN',
        cooperativeId: 'coop-1',
        status: 'ACTIVE',
      },
      permissions: ['inventory:read'],
    })
    vi.mocked(getCurrentUser).mockResolvedValue({
      id: 'user-1',
      username: 'coop_admin',
      displayName: '合作社管理员',
      role: 'COOPERATIVE_ADMIN',
      cooperativeId: 'coop-1',
      warehouseIds: ['warehouse-1'],
      permissions: ['inventory:read'],
      status: 'ACTIVE',
    })

    const store = useAuthStore()
    await Promise.all([store.initialize(), store.initialize()])

    expect(refresh).toHaveBeenCalledOnce()
    expect(getCurrentUser).toHaveBeenCalledOnce()
    expect(getAccessToken()).toBe('refreshed-token')
    expect(store.isAuthenticated).toBe(true)
    expect(store.user?.warehouseIds).toEqual(['warehouse-1'])
  })

  it('exposes a unified initialization error for non-401 failures', async () => {
    vi.mocked(refresh).mockRejectedValue(new Error('network unavailable'))

    const store = useAuthStore()
    await store.initialize()

    expect(store.isAuthenticated).toBe(false)
    expect(store.errorMessage).toBe('系统初始化失败，请稍后重试')
    expect(store.status).toBe('error')
  })
})
