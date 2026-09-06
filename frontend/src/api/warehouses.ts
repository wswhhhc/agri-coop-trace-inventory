import type { ApiResponse, ListResponse } from '@/types/api'
import type { WarehouseSummary } from '@/types/resources'

import http from './http'

export type WarehouseStatus = 'ACTIVE' | 'INACTIVE'

export interface WarehouseCreatePayload {
  cooperativeId?: string | null
  code: string
  name: string
  address: string | null
  managerName: string | null
}

export interface WarehouseUpdatePayload {
  name: string
  address: string | null
  managerName: string | null
  status: WarehouseStatus
}

export async function listWarehouses(): Promise<WarehouseSummary[]> {
  const response = await http.get<ListResponse<WarehouseSummary>>('/warehouses', {
    params: { page: 1, pageSize: 20 },
  })
  return response.data.data
}

export async function createWarehouse(
  payload: WarehouseCreatePayload,
): Promise<WarehouseSummary> {
  const response = await http.post<ApiResponse<WarehouseSummary>>('/warehouses', payload)
  return response.data.data
}

export async function updateWarehouse(
  warehouseId: string,
  payload: WarehouseUpdatePayload,
): Promise<WarehouseSummary> {
  const response = await http.patch<ApiResponse<WarehouseSummary>>(
    `/warehouses/${warehouseId}`,
    payload,
  )
  return response.data.data
}
