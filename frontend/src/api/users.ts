import type { ListResponse } from '@/types/api'
import type { UserSummary } from '@/types/resources'

import http from './http'

export async function listUsers(): Promise<UserSummary[]> {
  const response = await http.get<ListResponse<UserSummary>>('/users', {
    params: { page: 1, pageSize: 20 },
  })
  return response.data.data
}
