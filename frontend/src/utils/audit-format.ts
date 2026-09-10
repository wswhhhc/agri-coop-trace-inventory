const auditResultLabels: Record<string, string> = {
  SUCCESS: '成功',
  FAILURE: '失败',
}

const auditDateTimeFormatter = new Intl.DateTimeFormat('zh-CN', {
  timeZone: 'Asia/Shanghai',
  numberingSystem: 'latn',
  calendar: 'gregory',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hourCycle: 'h23',
})

export function formatAuditResult(value: string): string {
  return auditResultLabels[value] ?? '未知结果'
}

export function formatAuditDateTime(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '时间未知'

  const parts = Object.fromEntries(
    auditDateTimeFormatter.formatToParts(date).map(({ type, value: partValue }) => [type, partValue]),
  )
  return `${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute}:${parts.second}`
}
