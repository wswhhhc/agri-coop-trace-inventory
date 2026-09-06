import type { ListResponse } from '@/types/api'
import type { ProductCategorySummary } from '@/types/resources'

import http from './http'

export interface ProductCategoryListParams {
  page?: number
  pageSize?: number
  keyword?: string
  isActive?: boolean
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
