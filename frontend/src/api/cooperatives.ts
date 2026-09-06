import type { ListResponse } from '@/types/api'
import type { CooperativeSummary } from '@/types/resources'

import http from './http'

export async function listCooperatives(): Promise<CooperativeSummary[]> {
  const response = await http.get<ListResponse<CooperativeSummary>>('/cooperatives', {
    params: { page: 1, pageSize: 20 },
  })
  return response.data.data
}
