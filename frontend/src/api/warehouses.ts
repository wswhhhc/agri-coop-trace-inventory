import type { ApiResponse, ListResponse } from '@/types/api'
import type { WarehouseSummary } from '@/types/resources'

import http from './http'

export type WarehouseStatus = 'ACTIVE' | 'INACTIVE'

export interface WarehouseCreatePayload {
  cooperativeId?: string | null
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

export interface WarehouseListParams {
  page?: number
  pageSize?: number
}

export async function listWarehousesPage(
  options: WarehouseListParams = {},
): Promise<ListResponse<WarehouseSummary>> {
  const response = await http.get<ListResponse<WarehouseSummary>>('/warehouses', {
    params: { page: options.page ?? 1, pageSize: options.pageSize ?? 10 },
  })
  return response.data
}

export async function listWarehouses(options: WarehouseListParams = {}): Promise<WarehouseSummary[]> {
  return (await listWarehousesPage({ pageSize: options.pageSize ?? 100, ...options })).data
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
