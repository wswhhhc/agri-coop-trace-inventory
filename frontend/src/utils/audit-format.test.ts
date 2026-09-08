import { describe, expect, it } from 'vitest'

import { formatAuditResult } from './audit-format'

describe('formatAuditResult', () => {
  it('converts audit results to Chinese labels', () => {
    expect(formatAuditResult('SUCCESS')).toBe('成功')
    expect(formatAuditResult('FAILURE')).toBe('失败')
    expect(formatAuditResult('UNKNOWN')).toBe('未知结果')
  })
})
