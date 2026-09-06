export interface DashboardSummary {
  productCount: number
  batchCount: number
  inventoryByUnit: Array<{ unit: string; quantity: number }>
  pendingAlertCount: number
  expiringBatchCount: number
  lowStockProductCount: number
  updatedAt: string
}

export interface CooperativeSummary {
  id: string
  code: string
  name: string
  status: string
}

export interface UserSummary {
  id: string
  username: string
  displayName: string
  role: string
  cooperativeId: string | null
  status: string
}

export interface WarehouseSummary {
  id: string
  name: string
  code: string
  status: string
}

export interface ProductSummary {
  id: string
  code: string
  name: string
  unit: string
  isActive: boolean
}

export interface BatchSummary {
  id: string
  batchNo: string
  traceCode: string
  status: string
  productionDate: string
  expiryDate: string
}

export interface InventorySummary {
  id: string
  quantity: number
  availableQuantity: number
  warehouse: { id: string; name: string }
  product: { id: string; name: string; unit: string }
  batch: { id: string; batchNo: string; expiryDate: string }
  riskFlags: string[]
}

export interface InventoryTransactionSummary {
  id: string
  transactionNo: string
  operationNo: string
  transactionType: string
  quantity: number
  quantityDelta: number
  warehouseId: string
  batchId: string
  occurredAt: string
}

export interface AlertSummary {
  id: string
  alertType: string
  severity: string
  status: string
  title: string
  message: string
  detectedAt: string
}

export interface ForecastSummary {
  id: string
  warehouseId: string
  productId: string
  horizonDays: number
  predictedDemand: number
  currentStock: number
  recommendedReplenishment: number
  generatedAt: string
}

export interface AuditLogSummary {
  id: string
  action: string
  module: string
  resourceType: string
  result: string
  createdAt: string
}
