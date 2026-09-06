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
})
