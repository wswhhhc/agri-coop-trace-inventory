const TRACE_EVENT_TYPE_LABELS: Record<string, string> = {
  PRODUCTION: '生产',
  INSPECTION: '质检',
  INBOUND: '入库',
  OUTBOUND: '出库',
  TRANSFER: '调拨',
  OTHER: '其他',
}

const INSPECTION_CONCLUSION_LABELS: Record<string, string> = {
  PENDING: '待定',
  PASSED: '合格',
  FAILED: '不合格',
}

export function formatTraceEventType(value: string): string {
  return TRACE_EVENT_TYPE_LABELS[value] ?? '其他'
}

export function formatInspectionConclusion(value: string): string {
  return INSPECTION_CONCLUSION_LABELS[value] ?? '未知结论'
}
