import type { ListResponse } from '@/types/api'
import type { AuditLogSummary } from '@/types/resources'

import http from './http'

export async function listAuditLogs(): Promise<AuditLogSummary[]> {
  const response = await http.get<ListResponse<AuditLogSummary>>('/audit-logs', {
    params: { page: 1, pageSize: 20 },
  })
  return response.data.data
}
