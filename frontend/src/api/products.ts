import type { ListResponse } from '@/types/api'
import type { ApiResponse } from '@/types/api'
import type { ProductSummary, ProductUnit } from '@/types/resources'

import http from './http'

export interface ProductCreatePayload {
  categoryId: string
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

export interface ProductListParams {
  page?: number
  pageSize?: number
  isActive?: boolean
}

export async function listProducts(options: ProductListParams = {}): Promise<ListResponse<ProductSummary>> {
  const params = {
    page: options.page ?? 1,
    pageSize: options.pageSize ?? 10,
    ...(options.isActive === undefined ? {} : { isActive: options.isActive }),
  }
  const response = await http.get<ListResponse<ProductSummary>>('/products', {
    params,
  })
  return response.data
}

export async function listProductOptions(
  options: ProductListParams = {},
): Promise<ProductSummary[]> {
  const response = await listProducts(options)
  return response.data
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
