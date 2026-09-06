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
  address: string | null
  contactName: string | null
  contactPhone: string | null
  status: string
}

export interface UserSummary {
  id: string
  username: string
  displayName: string
  role: string
  cooperativeId: string | null
  warehouseIds: string[]
  phone: string | null
  status: string
}

export interface WarehouseSummary {
  id: string
  cooperativeId: string
  name: string
  code: string
  address: string | null
  managerName: string | null
  status: string
}

export type ProductUnit = 'KG' | 'TON' | 'BOX' | 'PIECE'

export interface ProductSummary {
  id: string
  code: string
  name: string
  categoryId: string
  unit: ProductUnit
  shelfLifeDays: number
  safetyStock: number
  isActive: boolean
}

export interface ProductCategorySummary {
  id: string
  code: string
  name: string
  description: string | null
  isActive: boolean
}

export interface BatchSummary {
  id: string
  productId: string
  batchNo: string
  traceCode: string
  origin: string
  status: string
  productionDate: string
  expiryDate: string
  responsiblePerson: string | null
}

export interface QualityInspectionItemSummary {
  id: string
  name: string
  value: string
  unit: string | null
  standard: string
  isQualified: boolean
  sortOrder: number
}

export interface QualityInspectionSummary {
  id: string
  batchId: string
  inspectionNo: string
  inspectionDate: string
  inspectorName: string
  conclusion: string
  remarks: string | null
  items: QualityInspectionItemSummary[]
  attachmentFileIds: string[]
}

export interface TraceEventSummary {
  id: string
  batchId: string
  eventType: string
  title: string
  description: string | null
  eventTime: string
  sourceType: string | null
  sourceId: string | null
}

export interface PublicTraceInspectionItemSummary {
  name: string
  value: string
  unit: string | null
  standard: string
  isQualified: boolean
}

export interface PublicTraceInspectionSummary {
  inspectionDate: string
  conclusion: string
  items: PublicTraceInspectionItemSummary[]
}

export interface PublicTraceSummary {
  traceCode: string
  product: { name: string; categoryName: string; unit: string; description: string | null }
  batch: {
    batchNo: string
    origin: string
    productionDate: string
    expiryDate: string
    status: string
  }
  latestInspection: PublicTraceInspectionSummary | null
  timeline: Array<{
    eventType: string
    title: string
    description: string
    occurredAt: string
  }>
  dataNotice: string
  updatedAt: string
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

export interface InventoryTransactionDetail extends InventoryTransactionSummary {
  transactionId: string
  operationId: string | null
  quantityBefore: number
  quantityAfter: number
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

export interface PermissionSummary {
  id: string
  code: string
  name: string
  module: string
  description: string | null
}

export interface RoleSummary {
  id: string
  code: string
  name: string
  description: string | null
  isSystem: boolean
  permissions: PermissionSummary[]
}
