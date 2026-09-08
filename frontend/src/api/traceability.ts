import type { ListResponse } from '@/types/api'
import type { TraceEventSummary } from '@/types/resources'

import http from './http'

export async function listTraceEvents(batchId: string): Promise<TraceEventSummary[]> {
  const response = await http.get<ListResponse<TraceEventSummary>>(
    `/batches/${batchId}/trace-events`,
    { params: { page: 1, pageSize: 10, sortBy: 'eventTime', sortOrder: 'ASC' } },
  )
  return response.data.data
}
