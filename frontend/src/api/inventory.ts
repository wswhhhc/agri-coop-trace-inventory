import type { ApiResponse, ListResponse } from '@/types/api'
import type { InventorySummary, InventoryTransactionSummary } from '@/types/resources'

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

export interface InventoryReceiptResult {
  transactionId: string
  transactionNo?: string
  quantityBefore?: number
  quantityAfter: number
}

export async function listInventory(): Promise<InventorySummary[]> {
  const response = await http.get<ListResponse<InventorySummary>>('/inventories', {
    params: { page: 1, pageSize: 20 },
  })
  return response.data.data
}

export async function listInventoryTransactions(): Promise<InventoryTransactionSummary[]> {
  const response = await http.get<ListResponse<InventoryTransactionSummary>>(
    '/inventory-transactions',
    { params: { page: 1, pageSize: 20 } },
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
