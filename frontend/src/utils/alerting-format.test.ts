import { describe, expect, it } from 'vitest'

import {
  formatAlertStatus,
  formatAlertType,
  formatSeverity,
  formatTaskStatus,
  formatEvidence,
} from './alerting-format'

describe('alerting display labels', () => {
  it('translates alert types into plain Chinese', () => {
    expect(formatAlertType('LOW_STOCK')).toBe('库存不足')
    expect(formatAlertType('QUALITY_FAILED')).toBe('质检异常')
  })

  it('translates severity and alert statuses', () => {
    expect(formatSeverity('HIGH')).toBe('高')
    expect(formatSeverity('CRITICAL')).toBe('严重')
    expect(formatAlertStatus('PENDING')).toBe('待处理')
    expect(formatAlertStatus('RESOLVED')).toBe('已解决')
  })

  it('translates task statuses and gives safe labels for unknown values', () => {
    expect(formatTaskStatus('RUNNING')).toBe('执行中')
    expect(formatTaskStatus('UNKNOWN')).toBe('未知状态')
    expect(formatAlertType('UNKNOWN')).toBe('未知预警类型')
  })

  it('formats evidence labels without exposing backend identifiers', () => {
    expect(
      formatEvidence({ availableQuantity: 12, thresholdQuantity: 20, inspectionId: 'secret-id' }),
    ).toEqual([
      { label: '可用库存', value: '12' },
      { label: '预警阈值', value: '20' },
    ])
  })
})
