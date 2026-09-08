import type { ApiResponse, ListResponse } from '@/types/api'
import type {
  AlertDetailSummary,
  AlertRuleSummary,
  AlertSummary,
  TaskSummary,
} from '@/types/resources'

import http from './http'

export interface AlertRuleUpdatePayload {
  thresholdQuantity?: number | null
  thresholdDays?: number | null
  turnoverDays?: number | null
  severity?: string
  isEnabled?: boolean
}

export interface AlertStatusUpdatePayload {
  status: string
  handlingNote: string | null
}

export interface AlertListParams {
  page?: number
  pageSize?: number
}

export async function listAlertsPage(
  options: AlertListParams = {},
): Promise<ListResponse<AlertSummary>> {
  const response = await http.get<ListResponse<AlertSummary>>('/alerts', {
    params: { page: options.page ?? 1, pageSize: options.pageSize ?? 10 },
  })
  return response.data
}

export async function listAlerts(options: AlertListParams = {}): Promise<AlertSummary[]> {
  return (await listAlertsPage(options)).data
}

export async function listAlertRulesPage(
  options: AlertListParams = {},
): Promise<ListResponse<AlertRuleSummary>> {
  const response = await http.get<ListResponse<AlertRuleSummary>>('/alert-rules', {
    params: { page: options.page ?? 1, pageSize: options.pageSize ?? 10 },
  })
  return response.data
}

export async function listAlertRules(options: AlertListParams = {}): Promise<AlertRuleSummary[]> {
  return (await listAlertRulesPage({ pageSize: options.pageSize ?? 100, ...options })).data
}

export async function getAlert(alertId: string): Promise<AlertDetailSummary> {
  const response = await http.get<ApiResponse<AlertDetailSummary>>(`/alerts/${alertId}`)
  return response.data.data
}

export async function updateAlert(
  alertId: string,
  payload: AlertStatusUpdatePayload,
): Promise<AlertDetailSummary> {
  const response = await http.patch<ApiResponse<AlertDetailSummary>>(
    `/alerts/${alertId}`,
    payload,
  )
  return response.data.data
}

export async function submitAlertScanTask(): Promise<TaskSummary> {
  const response = await http.post<ApiResponse<TaskSummary>>('/alert-scan-tasks')
  return response.data.data
}

export async function getTask(taskId: string): Promise<TaskSummary> {
  const response = await http.get<ApiResponse<TaskSummary>>(`/tasks/${taskId}`)
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
