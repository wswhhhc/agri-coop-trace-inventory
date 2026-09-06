import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { login as loginApi } from '@/api/auth'
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
})
