import type { ListResponse } from '@/types/api'
import type { ProductCategorySummary } from '@/types/resources'

import http from './http'

export interface ProductCategoryListParams {
  page?: number
  pageSize?: number
  keyword?: string
  isActive?: boolean
}

export interface ProductCategoryCreatePayload {
  code: string
  name: string
  description: string | null
}

export interface ProductCategoryUpdatePayload {
  name: string
  description: string | null
  isActive: boolean
}

export async function listProductCategories(
  options: ProductCategoryListParams = {},
): Promise<ProductCategorySummary[]> {
  const params = {
    page: options.page ?? 1,
    pageSize: options.pageSize ?? 20,
    ...(options.keyword ? { keyword: options.keyword } : {}),
    ...(options.isActive === undefined ? {} : { isActive: options.isActive }),
  }
  const response = await http.get<ListResponse<ProductCategorySummary>>('/product-categories', {
    params,
  })
  return response.data.data
}

export async function createProductCategory(
  payload: ProductCategoryCreatePayload,
): Promise<ProductCategorySummary> {
  const response = await http.post<{ data: ProductCategorySummary }>(
    '/product-categories',
    payload,
  )
  return response.data.data
}

export async function updateProductCategory(
  categoryId: string,
  payload: ProductCategoryUpdatePayload,
): Promise<ProductCategorySummary> {
  const response = await http.patch<{ data: ProductCategorySummary }>(
    `/product-categories/${categoryId}`,
    payload,
  )
  return response.data.data
}
