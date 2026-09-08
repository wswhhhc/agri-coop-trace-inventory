const auditResultLabels: Record<string, string> = {
  SUCCESS: '成功',
  FAILURE: '失败',
}

export function formatAuditResult(value: string): string {
  return auditResultLabels[value] ?? '未知结果'
}
