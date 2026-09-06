import { describe, expect, it } from 'vitest'

import {
  formatAlertSeverity,
  formatAlertType,
  getDefaultDashboardDateRange,
} from './dashboard-format'

describe('dashboard formatters', () => {
  it('translates known alert enums and keeps unknown values visible', () => {
    expect(formatAlertType('LOW_STOCK')).toBe('库存不足')
    expect(formatAlertSeverity('CRITICAL')).toBe('紧急')
    expect(formatAlertType('OTHER')).toBe('OTHER')
  })

  it('returns an inclusive 30-day default range', () => {
    expect(getDefaultDashboardDateRange(new Date(2026, 8, 6))).toEqual({
      startDate: '2026-08-08',
      endDate: '2026-09-06',
    })
  })
})
