import type { ApiResponse, ListResponse } from '@/types/api'
import type {
  InventorySummary,
  InventoryTransactionDetail,
  InventoryTransactionSummary,
} from '@/types/resources'

import http from './http'

export interface InventoryReceiptCreatePayload {
  warehouseId: string
  batchId: string
  quantity: number
  occurredAt: string
  referenceNo: string | null
  remark: string | null
}

export interface InventoryIssueCreatePayload extends InventoryReceiptCreatePayload {
  destination: string | null
}

export interface StocktakeCreatePayload {
  warehouseId: string
  batchId: string
  countedQuantity: number
  occurredAt: string
  reason: string
  remark: string | null
}

export interface InventoryLossCreatePayload {
  warehouseId: string
  batchId: string
  quantity: number
  occurredAt: string
  reason: string
  remark: string | null
}

export interface StockTransferCreatePayload {
  sourceWarehouseId: string
  targetWarehouseId: string
  batchId: string
  quantity: number
  occurredAt: string
  remark: string | null
}

export interface InventoryTransactionListParams {
  page?: number
  pageSize?: number
  warehouseId?: string
  batchId?: string
  transactionType?: string
}

export interface InventoryReceiptResult {
  transactionId: string
  transactionNo?: string
  quantityBefore?: number
  quantityAfter: number
}

export interface StocktakeResult {
  operationId?: string
  transactionId: string
  bookQuantity: number
  countedQuantity: number
  differenceQuantity: number
}

export interface StockTransferResult {
  transferId: string
  outTransactionId: string
  inTransactionId: string
}

export interface InventoryListParams {
  page?: number
  pageSize?: number
}

export async function listInventoryPage(
  options: InventoryListParams = {},
): Promise<ListResponse<InventorySummary>> {
  const response = await http.get<ListResponse<InventorySummary>>('/inventories', {
    params: { page: options.page ?? 1, pageSize: options.pageSize ?? 10 },
  })
  return response.data
}

export async function listInventory(
  options: InventoryListParams = {},
): Promise<InventorySummary[]> {
  return (await listInventoryPage({ pageSize: options.pageSize ?? 100, ...options })).data
}

export async function listInventoryTransactionsPage(
  options: InventoryTransactionListParams = {},
): Promise<ListResponse<InventoryTransactionSummary>> {
  const params = {
    page: options.page ?? 1,
    pageSize: options.pageSize ?? 10,
    ...(options.warehouseId ? { warehouseId: options.warehouseId } : {}),
    ...(options.batchId ? { batchId: options.batchId } : {}),
    ...(options.transactionType ? { transactionType: options.transactionType } : {}),
  }
  const response = await http.get<ListResponse<InventoryTransactionSummary>>(
    '/inventory-transactions',
    { params },
  )
  return response.data
}

export async function listInventoryTransactions(
  options: InventoryTransactionListParams = {},
): Promise<InventoryTransactionSummary[]> {
  return (await listInventoryTransactionsPage(options)).data
}

export async function getInventoryTransaction(
  transactionId: string,
): Promise<InventoryTransactionDetail> {
  const response = await http.get<ApiResponse<InventoryTransactionDetail>>(
    `/inventory-transactions/${transactionId}`,
  )
  return response.data.data
}

export async function createInventoryReceipt(
  payload: InventoryReceiptCreatePayload,
  idempotencyKey: string = crypto.randomUUID(),
): Promise<InventoryReceiptResult> {
  const response = await http.post<ApiResponse<InventoryReceiptResult>>(
    '/inventory-receipts',
    payload,
    { headers: { 'Idempotency-Key': idempotencyKey } },
  )
  return response.data.data
}

export async function createInventoryIssue(
  payload: InventoryIssueCreatePayload,
  idempotencyKey: string = crypto.randomUUID(),
): Promise<InventoryReceiptResult> {
  const response = await http.post<ApiResponse<InventoryReceiptResult>>(
    '/inventory-issues',
    payload,
    { headers: { 'Idempotency-Key': idempotencyKey } },
  )
  return response.data.data
}

export async function createStocktake(
  payload: StocktakeCreatePayload,
  idempotencyKey: string = crypto.randomUUID(),
): Promise<StocktakeResult> {
  const response = await http.post<ApiResponse<StocktakeResult>>(
    '/stocktakes',
    payload,
    { headers: { 'Idempotency-Key': idempotencyKey } },
  )
  return response.data.data
}

export async function createInventoryLoss(
  payload: InventoryLossCreatePayload,
  idempotencyKey: string = crypto.randomUUID(),
): Promise<InventoryReceiptResult> {
  const response = await http.post<ApiResponse<InventoryReceiptResult>>(
    '/inventory-losses',
    payload,
    { headers: { 'Idempotency-Key': idempotencyKey } },
  )
  return response.data.data
}

export async function createStockTransfer(
  payload: StockTransferCreatePayload,
  idempotencyKey: string = crypto.randomUUID(),
): Promise<StockTransferResult> {
  const response = await http.post<ApiResponse<StockTransferResult>>(
    '/stock-transfers',
    payload,
    { headers: { 'Idempotency-Key': idempotencyKey } },
  )
  return response.data.data
}
