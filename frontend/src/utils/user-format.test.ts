import { describe, expect, it } from 'vitest'

import { formatUserStatus } from './user-format'

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
