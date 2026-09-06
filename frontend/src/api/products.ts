import type { ListResponse } from '@/types/api'
import type { ApiResponse } from '@/types/api'
import type { ProductSummary, ProductUnit } from '@/types/resources'

import http from './http'

export interface ProductCreatePayload {
  categoryId: string
  code: string
  name: string
  unit: ProductUnit
  shelfLifeDays: number
  safetyStock: number
}

export interface ProductUpdatePayload {
  name: string
  unit: ProductUnit
  shelfLifeDays: number
  safetyStock: number
  isActive: boolean
}

export async function listProducts(): Promise<ProductSummary[]> {
  const response = await http.get<ListResponse<ProductSummary>>('/products', {
    params: { page: 1, pageSize: 20 },
  })
  return response.data.data
}

export async function createProduct(payload: ProductCreatePayload): Promise<ProductSummary> {
  const response = await http.post<ApiResponse<ProductSummary>>('/products', payload)
  return response.data.data
}

export async function updateProduct(
  productId: string,
  payload: ProductUpdatePayload,
): Promise<ProductSummary> {
  const response = await http.patch<ApiResponse<ProductSummary>>(
    `/products/${productId}`,
    payload,
  )
  return response.data.data
}
