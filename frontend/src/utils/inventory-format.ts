const inventoryRiskLabels: Record<string, string> = {
  LOW_STOCK: '库存不足',
  NEAR_EXPIRY: '临近过期',
  OVERSTOCK: '库存积压',
}

export function formatInventoryRisk(value: string): string {
  return inventoryRiskLabels[value] ?? '未知风险'
}

export function formatInventoryRiskFlags(values: string[]): string {
  return values.map(formatInventoryRisk).join('、') || '正常'
}
