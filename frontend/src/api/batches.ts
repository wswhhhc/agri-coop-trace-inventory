import type { ListResponse } from '@/types/api'
import type { BatchSummary } from '@/types/resources'

import http from './http'

export async function listBatches(): Promise<BatchSummary[]> {
  const response = await http.get<ListResponse<BatchSummary>>('/batches', {
    params: { page: 1, pageSize: 20 },
  })
  return response.data.data
}
