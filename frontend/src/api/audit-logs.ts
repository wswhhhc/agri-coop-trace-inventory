import type { ListResponse } from '@/types/api'
import type { AuditLogSummary } from '@/types/resources'
import { cleanQueryParams } from '@/composables/usePageData'

import http from './http'

export interface AuditLogListParams {
  page?: number
  pageSize?: number
  userId?: string
  action?: string
  resourceType?: string
  resourceId?: string
  result?: 'SUCCESS' | 'FAILURE'
  startDate?: string
  endDate?: string
}

export async function listAuditLogsPage(
  params: AuditLogListParams = {},
): Promise<ListResponse<AuditLogSummary>> {
  const query = cleanQueryParams({
    page: params.page ?? 1,
    pageSize: params.pageSize ?? 10,
    userId: params.userId,
    action: params.action,
    resourceType: params.resourceType,
    resourceId: params.resourceId,
    result: params.result,
    startDate: params.startDate,
    endDate: params.endDate,
  })
  const response = await http.get<ListResponse<AuditLogSummary>>('/audit-logs', {
    params: query,
  })
  return response.data
}

export async function listAuditLogs(
  params: AuditLogListParams = {},
): Promise<AuditLogSummary[]> {
  return (await listAuditLogsPage(params)).data
}

export async function getAuditLog(auditLogId: string): Promise<AuditLogSummary> {
  const response = await http.get<{ data: AuditLogSummary }>(`/audit-logs/${auditLogId}`)
  return response.data.data
}
