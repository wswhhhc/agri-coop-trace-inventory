export interface DashboardQueryParams {
  warehouseId?: string
  startDate?: string
  endDate?: string
}

export interface ProductRankingParams extends DashboardQueryParams {
  limit?: number
}

export interface InventoryUnitSummary {
  unit: string
  quantity: number
}

export interface DashboardSummary {
  productCount: number
  batchCount: number
  inventoryByUnit: InventoryUnitSummary[]
  pendingAlertCount: number
  expiringBatchCount: number
  lowStockProductCount: number
  updatedAt: string
}

export interface InventoryTrend {
  date: string
  unit: string
  inboundQuantity: number
  outboundQuantity: number
  endingQuantity: number
}

export interface AlertDistributionItem {
  alertType: string
  severity: string
  count: number
}

export interface AlertDistribution {
  totalCount: number
  items: AlertDistributionItem[]
}

export interface ProductRankingItem {
  productId: string
  productName: string
  unit: string
  outboundQuantity: number
  outboundCount: number
}

export interface ForecastComparisonItem {
  forecastResultId: string
  warehouseId: string
  productId: string
  modelVersionId: string
  modelVersion: string
  forecastStartDate: string
  forecastEndDate: string
  predictedDemand: number
  actualDemand: number
  absoluteError: number
  metrics: Record<string, number>
}
