import { describe, expect, it } from 'vitest'

import { canManageAlertRules } from './alerting-permission'

describe('canManageAlertRules', () => {
  it('allows only cooperative administrators with alert read permission', () => {
    expect(canManageAlertRules('COOPERATIVE_ADMIN', ['alert:read'])).toBe(true)
    expect(canManageAlertRules('WAREHOUSE_STAFF', ['alert:read'])).toBe(false)
    expect(canManageAlertRules('COOPERATIVE_ADMIN', [])).toBe(false)
  })
})
