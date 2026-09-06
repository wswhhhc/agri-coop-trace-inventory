import type { ApiResponse } from '@/types/api'
import type { PublicTraceSummary } from '@/types/resources'

import http from './http'

export async function getPublicTrace(traceCode: string): Promise<PublicTraceSummary> {
  const response = await http.get<ApiResponse<PublicTraceSummary>>(
    `/public/traces/${encodeURIComponent(traceCode)}`,
  )
  return response.data.data
}
