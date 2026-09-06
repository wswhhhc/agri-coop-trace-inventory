import type { ListResponse } from '@/types/api'
import type { WarehouseSummary } from '@/types/resources'

import http from './http'

export async function listWarehouses(): Promise<WarehouseSummary[]> {
  const response = await http.get<ListResponse<WarehouseSummary>>('/warehouses', {
    params: { page: 1, pageSize: 20 },
  })
  return response.data.data
}
