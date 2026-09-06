const alertTypeLabels: Record<string, string> = {
  LOW_STOCK: '库存不足',
  NEAR_EXPIRY: '临近过期',
  OVERSTOCK: '库存积压',
  QUALITY_FAILED: '质检不合格',
}

const severityLabels: Record<string, string> = {
  LOW: '低',
  MEDIUM: '中',
  HIGH: '高',
  CRITICAL: '紧急',
}

export function formatAlertType(alertType: string): string {
  return alertTypeLabels[alertType] ?? alertType
}

export function formatAlertSeverity(severity: string): string {
  return severityLabels[severity] ?? severity
}

export function formatDashboardNumber(value: number): string {
  return new Intl.NumberFormat('zh-CN', { maximumFractionDigits: 2 }).format(value)
}

export function getDefaultDashboardDateRange(today = new Date()): {
  startDate: string
  endDate: string
} {
  const endDate = new Date(today)
  const startDate = new Date(today)
  startDate.setDate(startDate.getDate() - 29)

  return {
    startDate: formatDateInput(startDate),
    endDate: formatDateInput(endDate),
  }
}

function formatDateInput(value: Date): string {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
