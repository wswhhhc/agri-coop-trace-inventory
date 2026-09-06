import { beforeEach, describe, expect, it, vi } from 'vitest'

import http from './http'
import { listPermissions, listRoles, updateRolePermissions } from './roles'

vi.mock('./http', () => ({
  default: { get: vi.fn(), put: vi.fn() },
}))

describe('roles api', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('lists roles and permissions', async () => {
    vi.mocked(http.get)
      .mockResolvedValueOnce({ data: { data: [] } })
      .mockResolvedValueOnce({ data: { data: [] } })

    await expect(listRoles()).resolves.toEqual([])
    await expect(listPermissions()).resolves.toEqual([])
    expect(http.get).toHaveBeenNthCalledWith(1, '/roles', {
      params: { page: 1, pageSize: 100 },
    })
    expect(http.get).toHaveBeenNthCalledWith(2, '/roles/permissions', {
      params: { page: 1, pageSize: 100 },
    })
  })

  it('updates role permissions', async () => {
    const permissions = ['user:manage', 'warehouse:manage']
    vi.mocked(http.put).mockResolvedValueOnce({
      data: { data: { id: 'role-1', code: 'SYSTEM_ADMIN', permissions: [] } },
    })

    await expect(updateRolePermissions('role-1', permissions)).resolves.toMatchObject({ id: 'role-1' })
    expect(http.put).toHaveBeenCalledWith('/roles/role-1/permissions', {
      permissionCodes: permissions,
    })
  })
})
