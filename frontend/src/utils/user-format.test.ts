import { describe, expect, it } from 'vitest'

import { formatUserRole, formatUserStatus } from './user-format'

describe('formatUserRole', () => {
  it('translates user roles into Chinese labels', () => {
    expect(formatUserRole('SYSTEM_ADMIN')).toBe('系统管理员')
    expect(formatUserRole('COOPERATIVE_ADMIN')).toBe('合作社管理员')
    expect(formatUserRole('WAREHOUSE_STAFF')).toBe('仓库工作人员')
  })

  it('keeps unknown roles visible for forward compatibility', () => {
    expect(formatUserRole('AUDITOR')).toBe('AUDITOR')
  })
})

describe('formatUserStatus', () => {
  it('translates user statuses into Chinese labels', () => {
    expect(formatUserStatus('ACTIVE')).toBe('启用')
    expect(formatUserStatus('LOCKED')).toBe('锁定')
    expect(formatUserStatus('INACTIVE')).toBe('停用')
  })

  it('keeps unknown statuses visible for forward compatibility', () => {
    expect(formatUserStatus('PENDING')).toBe('PENDING')
  })
})
