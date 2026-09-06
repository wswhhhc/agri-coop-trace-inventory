import type { ListResponse } from '@/types/api'
import type { AlertSummary } from '@/types/resources'

import http from './http'

export async function listAlerts(): Promise<AlertSummary[]> {
  const response = await http.get<ListResponse<AlertSummary>>('/alerts', {
    params: { page: 1, pageSize: 20 },
  })
  return response.data.data
}
