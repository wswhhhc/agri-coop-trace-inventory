import type { ApiResponse, ListResponse } from '@/types/api'
import type { AlertRuleSummary, AlertSummary } from '@/types/resources'

import http from './http'

export interface AlertRuleUpdatePayload {
  thresholdQuantity?: number | null
  thresholdDays?: number | null
  turnoverDays?: number | null
  severity?: string
  isEnabled?: boolean
}

export async function listAlerts(): Promise<AlertSummary[]> {
  const response = await http.get<ListResponse<AlertSummary>>('/alerts', {
    params: { page: 1, pageSize: 20 },
  })
  return response.data.data
}

export async function listAlertRules(): Promise<AlertRuleSummary[]> {
  const response = await http.get<ListResponse<AlertRuleSummary>>('/alert-rules', {
    params: { page: 1, pageSize: 100 },
  })
  return response.data.data
}

export async function updateAlertRule(
  ruleId: string,
  payload: AlertRuleUpdatePayload,
): Promise<AlertRuleSummary> {
  const response = await http.patch<ApiResponse<AlertRuleSummary>>(
    `/alert-rules/${ruleId}`,
    payload,
  )
  return response.data.data
}
