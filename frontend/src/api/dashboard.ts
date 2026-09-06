import type { ApiResponse } from '@/types/api'
import type { DashboardSummary } from '@/types/resources'

import http from './http'

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const response = await http.get<ApiResponse<DashboardSummary>>('/dashboard/summary')
  return response.data.data
}
