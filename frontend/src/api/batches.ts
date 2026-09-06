import type { ApiResponse, ListResponse } from '@/types/api'
import type { BatchSummary } from '@/types/resources'

import http from './http'

export interface BatchCreatePayload {
  productId: string
  batchNo: string
  origin: string
  productionDate: string
  expiryDate: string
  responsiblePerson: string | null
}

export type BatchStatus = 'CREATED' | 'IN_STOCK' | 'DEPLETED' | 'BLOCKED' | 'EXPIRED'

export interface BatchUpdatePayload {
  origin: string
  expiryDate: string
  responsiblePerson: string | null
  status: BatchStatus
}

export async function listBatches(): Promise<BatchSummary[]> {
  const response = await http.get<ListResponse<BatchSummary>>('/batches', {
    params: { page: 1, pageSize: 20 },
  })
  return response.data.data
}

export async function getBatch(batchId: string): Promise<BatchSummary> {
  const response = await http.get<ApiResponse<BatchSummary>>(`/batches/${batchId}`)
  return response.data.data
}

export async function updateBatch(
  batchId: string,
  payload: BatchUpdatePayload,
): Promise<BatchSummary> {
  const response = await http.patch<ApiResponse<BatchSummary>>(`/batches/${batchId}`, payload)
  return response.data.data
}

export async function createBatch(payload: BatchCreatePayload): Promise<BatchSummary> {
  const response = await http.post<ApiResponse<BatchSummary>>('/batches', payload)
  return response.data.data
}
