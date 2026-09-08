import { describe, expect, it } from 'vitest'

import { formatBatchStatus } from './batch-format'

describe('formatBatchStatus', () => {
  it.each([
    ['CREATED', '已创建'],
    ['IN_STOCK', '库存中'],
    ['DEPLETED', '已耗尽'],
    ['BLOCKED', '已冻结'],
    ['EXPIRED', '已过期'],
  ])('converts %s to %s', (value, label) => {
    expect(formatBatchStatus(value)).toBe(label)
  })

  it('uses a Chinese fallback for an unknown status', () => {
    expect(formatBatchStatus('UNKNOWN')).toBe('未知状态')
  })
})
