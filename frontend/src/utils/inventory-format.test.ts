import { describe, expect, it } from 'vitest'

import { formatInventoryRisk, formatInventoryRiskFlags } from './inventory-format'

describe('inventory formatters', () => {
  it.each([
    ['LOW_STOCK', '库存不足'],
    ['NEAR_EXPIRY', '临近过期'],
    ['OVERSTOCK', '库存积压'],
  ])('converts %s to %s', (value, label) => {
    expect(formatInventoryRisk(value)).toBe(label)
  })

  it('formats multiple risks and the normal state', () => {
    expect(formatInventoryRiskFlags(['LOW_STOCK', 'NEAR_EXPIRY'])).toBe('库存不足、临近过期')
    expect(formatInventoryRiskFlags([])).toBe('正常')
  })
})
