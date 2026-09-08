import type { ListResponse } from '@/types/api'
import type { TraceEventSummary } from '@/types/resources'
import { cleanQueryParams } from '@/composables/usePageData'

import http from './http'

export interface TraceEventListParams {
  page?: number
  pageSize?: number
  eventType?: string
  sortBy?: string
  sortOrder?: 'ASC' | 'DESC'
}

export async function listTraceEventsPage(
  batchId: string,
  options: TraceEventListParams = {},
): Promise<ListResponse<TraceEventSummary>> {
  const params = cleanQueryParams({
    page: options.page ?? 1,
    pageSize: options.pageSize ?? 10,
    eventType: options.eventType,
    sortBy: options.sortBy ?? 'eventTime',
    sortOrder: options.sortOrder ?? 'ASC',
  })
  const response = await http.get<ListResponse<TraceEventSummary>>(
    `/batches/${batchId}/trace-events`,
    { params },
  )
  return response.data
}

export async function listTraceEvents(batchId: string): Promise<TraceEventSummary[]> {
  return (await listTraceEventsPage(batchId)).data
}
