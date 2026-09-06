import { describe, expect, it } from 'vitest'

import { resolveRouteAccess } from './guards'

describe('route access guard', () => {
  it('redirects unauthenticated users to login with their original path', () => {
    expect(
      resolveRouteAccess(
        { fullPath: '/inventory', meta: { requiresAuth: true } },
        { isAuthenticated: false, role: null, permissions: [] },
      ),
    ).toEqual({ name: 'login', query: { redirect: '/inventory' } })
  })

  it('allows unauthenticated users to open public trace pages', () => {
    expect(
      resolveRouteAccess(
        { fullPath: '/trace/tr_ABC123', meta: {} },
        { isAuthenticated: false, role: null, permissions: [] },
      ),
    ).toBe(true)
  })

  it('redirects authenticated users away from login', () => {
    expect(
      resolveRouteAccess(
        { fullPath: '/login', meta: { guestOnly: true } },
        { isAuthenticated: true, role: 'SYSTEM_ADMIN', permissions: [] },
      ),
    ).toEqual({ name: 'dashboard' })
  })

  it('redirects authenticated users without route access to forbidden', () => {
    expect(
      resolveRouteAccess(
        {
          fullPath: '/users',
          meta: { requiresAuth: true, roles: ['SYSTEM_ADMIN'], permissions: ['user:manage'] },
        },
        { isAuthenticated: true, role: 'WAREHOUSE_STAFF', permissions: [] },
      ),
    ).toEqual({ name: 'forbidden' })
  })

  it('requires both an allowed dashboard role and inventory read permission', () => {
    expect(
      resolveRouteAccess(
        {
          fullPath: '/dashboard',
          meta: {
            requiresAuth: true,
            roles: ['SYSTEM_ADMIN', 'COOPERATIVE_ADMIN', 'WAREHOUSE_STAFF'],
            permissions: ['inventory:read'],
          },
        },
        { isAuthenticated: true, role: 'PUBLIC', permissions: ['inventory:read'] },
      ),
    ).toEqual({ name: 'forbidden' })

    expect(
      resolveRouteAccess(
        {
          fullPath: '/dashboard',
          meta: {
            requiresAuth: true,
            roles: ['SYSTEM_ADMIN', 'COOPERATIVE_ADMIN', 'WAREHOUSE_STAFF'],
            permissions: ['inventory:read'],
          },
        },
        { isAuthenticated: true, role: 'WAREHOUSE_STAFF', permissions: [] },
      ),
    ).toEqual({ name: 'forbidden' })
  })
})
