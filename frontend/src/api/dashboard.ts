import type { ApiResponse } from '@/types/api'
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
  params: DashboardQueryParams = {},
): Promise<InventoryTrend[]> {
  const response = await http.get<ApiResponse<InventoryTrend[]>>('/dashboard/inventory-trends', {
    params,
  })
  return response.data.data
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
