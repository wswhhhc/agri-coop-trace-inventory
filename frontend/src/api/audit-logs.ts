import type { ListResponse } from '@/types/api'
import type { AuditLogSummary } from '@/types/resources'

import http from './http'

export interface AuditLogListParams {
  action?: string
  resourceType?: string
  resourceId?: string
  result?: 'SUCCESS' | 'FAILURE'
  startDate?: string
  endDate?: string
}

export async function listAuditLogs(
  params: AuditLogListParams = {},
): Promise<AuditLogSummary[]> {
  const response = await http.get<ListResponse<AuditLogSummary>>('/audit-logs', {
    params: { page: 1, pageSize: 20, ...params },
  })
  return response.data.data
}

export async function getAuditLog(auditLogId: string): Promise<AuditLogSummary> {
  const response = await http.get<{ data: AuditLogSummary }>(`/audit-logs/${auditLogId}`)
  return response.data.data
}
