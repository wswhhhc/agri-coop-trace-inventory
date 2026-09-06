import type { ListResponse } from '@/types/api'
import type { ProductSummary } from '@/types/resources'

import http from './http'

export async function listProducts(): Promise<ProductSummary[]> {
  const response = await http.get<ListResponse<ProductSummary>>('/products', {
    params: { page: 1, pageSize: 20 },
  })
  return response.data.data
}
