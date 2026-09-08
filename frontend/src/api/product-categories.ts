import type { ListResponse } from '@/types/api'
import type { ProductCategorySummary } from '@/types/resources'
import { cleanQueryParams } from '@/composables/usePageData'

import http from './http'

export interface ProductCategoryListParams {
  page?: number
  pageSize?: number
  keyword?: string
  isActive?: boolean
}

export interface ProductCategoryCreatePayload {
  name: string
  description: string | null
}

export interface ProductCategoryUpdatePayload {
  name: string
  description: string | null
  isActive: boolean
}

export async function listProductCategoriesPage(
  options: ProductCategoryListParams = {},
): Promise<ListResponse<ProductCategorySummary>> {
  const params = cleanQueryParams({
    page: options.page ?? 1,
    pageSize: options.pageSize ?? 10,
    keyword: options.keyword,
    isActive: options.isActive,
  })
  const response = await http.get<ListResponse<ProductCategorySummary>>('/product-categories', {
    params,
  })
  return response.data
}

export async function listProductCategories(
  options: ProductCategoryListParams = {},
): Promise<ProductCategorySummary[]> {
  return (await listProductCategoriesPage({ pageSize: options.pageSize ?? 100, ...options })).data
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
