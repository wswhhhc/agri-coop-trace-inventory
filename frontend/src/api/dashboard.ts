import type { ApiResponse, ListResponse } from '@/types/api'
import type {
  AlertDistribution,
  DashboardQueryParams,
  DashboardSummary,
  InventoryTrend,
  ProductRankingItem,
  ProductRankingParams,
} from '@/types/dashboard'

import http from './http'

export async function getDashboardSummary(
  params: DashboardQueryParams = {},
): Promise<DashboardSummary> {
  const response = await http.get<ApiResponse<DashboardSummary>>('/dashboard/summary', { params })
  return response.data.data
}

export async function getInventoryTrends(
  params: DashboardListParams = {},
): Promise<InventoryTrend[]> {
  const response = await listInventoryTrendsPage(params)
  return response.data
}

export interface DashboardListParams extends DashboardQueryParams {
  page?: number
  pageSize?: number
}

export async function listInventoryTrendsPage(
  options: DashboardListParams = {},
): Promise<ListResponse<InventoryTrend>> {
  const params = {
    page: options.page ?? 1,
    pageSize: options.pageSize ?? 20,
    ...(options.warehouseId ? { warehouseId: options.warehouseId } : {}),
    ...(options.startDate ? { startDate: options.startDate } : {}),
    ...(options.endDate ? { endDate: options.endDate } : {}),
  }
  const response = await http.get<ListResponse<InventoryTrend>>('/dashboard/inventory-trends', {
    params,
  })
  return response.data
}

export async function getAlertDistribution(
  params: DashboardQueryParams = {},
): Promise<AlertDistribution> {
  const response = await http.get<ApiResponse<AlertDistribution>>('/dashboard/alert-distribution', {
    params,
  })
  return response.data.data
}

export async function getProductRanking(
  params: ProductRankingParams = {},
): Promise<ProductRankingItem[]> {
  const response = await http.get<ApiResponse<ProductRankingItem[]>>('/dashboard/product-ranking', {
    params,
  })
  return response.data.data
}
