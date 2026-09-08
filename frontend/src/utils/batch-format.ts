const batchStatusLabels: Record<string, string> = {
  CREATED: '已创建',
  IN_STOCK: '库存中',
  DEPLETED: '已耗尽',
  BLOCKED: '已冻结',
  EXPIRED: '已过期',
}

export function formatBatchStatus(value: string): string {
  return batchStatusLabels[value] ?? '未知状态'
}
