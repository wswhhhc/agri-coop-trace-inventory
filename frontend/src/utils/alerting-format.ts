const ALERT_TYPE_LABELS: Record<string, string> = {
  LOW_STOCK: '库存不足',
  NEAR_EXPIRY: '临近过期',
  OVERSTOCK: '库存积压',
  QUALITY_FAILED: '质检异常',
}

const SEVERITY_LABELS: Record<string, string> = {
  LOW: '低',
  MEDIUM: '中',
  HIGH: '高',
  CRITICAL: '严重',
}

const ALERT_STATUS_LABELS: Record<string, string> = {
  PENDING: '待处理',
  PROCESSING: '处理中',
  RESOLVED: '已解决',
  IGNORED: '已忽略',
}

const TASK_STATUS_LABELS: Record<string, string> = {
  PENDING: '等待中',
  RUNNING: '执行中',
  SUCCESS: '已完成',
  FAILURE: '执行失败',
  RETRY: '重试中',
}

const EVIDENCE_LABELS: Record<string, string> = {
  availableQuantity: '可用库存',
  thresholdQuantity: '预警阈值',
  expiryDate: '到期日期',
  daysRemaining: '剩余天数',
  thresholdDays: '天数阈值',
  quantity: '库存数量',
  daysInStock: '库存天数',
  turnoverDays: '周转天数',
  conclusion: '质检结论',
}

export function formatAlertType(value: string): string {
  return ALERT_TYPE_LABELS[value] ?? '未知预警类型'
}

export function formatSeverity(value: string): string {
  return SEVERITY_LABELS[value] ?? '未知级别'
}

export function formatAlertStatus(value: string): string {
  return ALERT_STATUS_LABELS[value] ?? '未知状态'
}

export function formatTaskStatus(value: string): string {
  return TASK_STATUS_LABELS[value] ?? '未知状态'
}

export function formatEvidence(
  evidence: Record<string, unknown>,
): Array<{ label: string; value: string }> {
  return Object.entries(evidence)
    .filter(([key]) => !key.toLowerCase().endsWith('id'))
    .filter(([key]) => EVIDENCE_LABELS[key])
    .map(([key, value]) => ({
      label: EVIDENCE_LABELS[key],
      value: value === null || value === undefined ? '—' : String(value),
    }))
}

export function formatDateTime(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '时间未知'
  return new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}
