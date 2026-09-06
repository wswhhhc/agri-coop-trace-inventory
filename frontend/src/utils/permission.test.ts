import { describe, expect, it } from 'vitest'

import { hasRequiredAccess, type AccessSubject } from './permission'

const cooperativeAdmin: AccessSubject = {
  role: 'COOPERATIVE_ADMIN',
  permissions: ['inventory:read', 'product:manage'],
}

describe('permission utilities', () => {
  it('requires both a matching role and all declared permissions', () => {
    expect(
      hasRequiredAccess(cooperativeAdmin, {
        roles: ['COOPERATIVE_ADMIN'],
        permissions: ['inventory:read'],
      }),
    ).toBe(true)

    expect(
      hasRequiredAccess(cooperativeAdmin, {
        roles: ['SYSTEM_ADMIN'],
        permissions: ['inventory:read'],
      }),
    ).toBe(false)

    expect(
      hasRequiredAccess(cooperativeAdmin, {
        roles: ['COOPERATIVE_ADMIN'],
        permissions: ['inventory:write'],
      }),
    ).toBe(false)
  })

  it('allows an authenticated subject when a route declares no restrictions', () => {
    expect(hasRequiredAccess(cooperativeAdmin, {})).toBe(true)
  })
})
