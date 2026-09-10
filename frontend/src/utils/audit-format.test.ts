import { describe, expect, it } from 'vitest'

import { formatAuditDateTime, formatAuditResult } from './audit-format'

describe('formatAuditResult', () => {
  it('converts audit results to Chinese labels', () => {
    expect(formatAuditResult('SUCCESS')).toBe('成功')
    expect(formatAuditResult('FAILURE')).toBe('失败')
    expect(formatAuditResult('UNKNOWN')).toBe('未知结果')
  })
})

describe('formatAuditDateTime', () => {
  it('converts UTC audit timestamps to China Standard Time', () => {
    expect(formatAuditDateTime('2026-09-10T05:01:51.823467Z')).toBe('2026-09-10 13:01:51')
  })

  it('returns a safe label for invalid timestamps', () => {
    expect(formatAuditDateTime('invalid')).toBe('时间未知')
  })
})
