import { describe, expect, it } from 'vitest'

import { filterMenuItems, menuItems } from './menu'

describe('menu configuration', () => {
  it('filters platform and business entries by role and permissions', () => {
    const cooperativeAdminMenu = filterMenuItems(menuItems, {
      role: 'COOPERATIVE_ADMIN',
      permissions: ['user:manage', 'product:manage', 'inventory:read', 'alert:read', 'model:read', 'audit:read'],
    })
    const paths = cooperativeAdminMenu.map((item) => item.path)

    expect(paths).toContain('/dashboard')
    expect(paths).toContain('/products')
    expect(paths).not.toContain('/cooperatives')
    expect(paths).not.toContain('/roles')
  })

  it('keeps warehouse staff away from platform administration entries', () => {
    const warehouseMenu = filterMenuItems(menuItems, {
      role: 'WAREHOUSE_STAFF',
      permissions: ['batch:manage', 'inventory:read', 'inventory:write', 'alert:read', 'model:read'],
    })
    const paths = warehouseMenu.map((item) => item.path)

    expect(paths).toContain('/inventory')
    expect(paths).toContain('/batches')
    expect(paths).not.toContain('/users')
    expect(paths).not.toContain('/roles')
  })
})
