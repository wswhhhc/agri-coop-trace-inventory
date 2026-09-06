import { beforeEach, describe, expect, it, vi } from 'vitest'

import http from './http'
import {
  createUser,
  listUsers,
  replaceUserWarehouses,
  resetUserPassword,
  updateUser,
} from './users'

vi.mock('./http', () => ({
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), put: vi.fn() },
}))

describe('users api', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('lists users with pagination', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({ data: { data: [] } })

    await expect(listUsers()).resolves.toEqual([])
    expect(http.get).toHaveBeenCalledWith('/users', {
      params: { page: 1, pageSize: 20 },
    })
  })

  it('creates a user and returns the initial password', async () => {
    const payload = {
      username: 'staff01',
      displayName: '仓库员工',
      role: 'WAREHOUSE_STAFF',
      cooperativeId: 'cooperative-1',
      warehouseIds: [],
      phone: '13800138000',
    }
    vi.mocked(http.post).mockResolvedValueOnce({
      data: { data: { id: 'user-1', ...payload, status: 'ACTIVE', initialPassword: 'temporary-1' } },
    })

    await expect(createUser(payload)).resolves.toMatchObject({
      id: 'user-1',
      initialPassword: 'temporary-1',
    })
    expect(http.post).toHaveBeenCalledWith('/users', payload)
  })

  it('updates user profile, role and status', async () => {
    const payload = {
      displayName: '仓库员工（锁定）',
      role: 'WAREHOUSE_STAFF',
      status: 'LOCKED' as const,
      phone: null,
    }
    vi.mocked(http.patch).mockResolvedValueOnce({ data: { data: { id: 'user-1', ...payload } } })

    await expect(updateUser('user-1', payload)).resolves.toMatchObject({
      id: 'user-1',
      status: 'LOCKED',
    })
    expect(http.patch).toHaveBeenCalledWith('/users/user-1', payload)
  })

  it('replaces a warehouse staff user warehouse assignment', async () => {
    const payload = { warehouseIds: ['warehouse-1', 'warehouse-2'] }
    vi.mocked(http.put).mockResolvedValueOnce({
      data: { data: { id: 'user-1', warehouseIds: payload.warehouseIds } },
    })

    await expect(replaceUserWarehouses('user-1', payload)).resolves.toMatchObject({
      id: 'user-1',
      warehouseIds: payload.warehouseIds,
    })
    expect(http.put).toHaveBeenCalledWith('/users/user-1/warehouses', payload)
  })

  it('resets a user password', async () => {
    vi.mocked(http.post).mockResolvedValueOnce({
      data: { data: { temporaryPassword: 'temporary-2' } },
    })

    await expect(resetUserPassword('user-1')).resolves.toEqual({
      temporaryPassword: 'temporary-2',
    })
    expect(http.post).toHaveBeenCalledWith('/users/user-1/password-resets')
  })
})
