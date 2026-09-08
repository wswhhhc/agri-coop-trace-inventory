import { describe, expect, it } from 'vitest'

import { formatTraceEventType, formatInspectionConclusion } from './traceability-format'

describe('traceability formatters', () => {
  it('将追溯事件类型转换为中文', () => {
    expect(formatTraceEventType('OTHER')).toBe('其他')
    expect(formatTraceEventType('INBOUND')).toBe('入库')
  })

  it('将质检结论转换为中文', () => {
    expect(formatInspectionConclusion('PASSED')).toBe('合格')
    expect(formatInspectionConclusion('FAILED')).toBe('不合格')
  })
})
