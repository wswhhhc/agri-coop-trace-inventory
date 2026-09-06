import type { ListResponse } from '@/types/api'
import type { ForecastSummary } from '@/types/resources'

import http from './http'

export async function listForecastResults(): Promise<ForecastSummary[]> {
  const response = await http.get<ListResponse<ForecastSummary>>('/forecast-results', {
    params: { page: 1, pageSize: 20 },
  })
  return response.data.data
}
