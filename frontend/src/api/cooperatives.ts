import type { ApiResponse, ListResponse } from '@/types/api'
import type { CooperativeSummary } from '@/types/resources'

import http from './http'

export type CooperativeStatus = 'ACTIVE' | 'INACTIVE'

export interface CooperativeCreatePayload {
  name: string
  address: string | null
  contactName: string | null
  contactPhone: string | null
}

export interface CooperativeUpdatePayload {
  name: string
  address: string | null
  contactName: string | null
  contactPhone: string | null
  status: CooperativeStatus
}

export interface CooperativeListParams {
  page?: number
  pageSize?: number
}

export async function listCooperativesPage(
  options: CooperativeListParams = {},
): Promise<ListResponse<CooperativeSummary>> {
  const response = await http.get<ListResponse<CooperativeSummary>>('/cooperatives', {
    params: { page: options.page ?? 1, pageSize: options.pageSize ?? 10 },
  })
  return response.data
}

export async function listCooperatives(
  options: CooperativeListParams = {},
): Promise<CooperativeSummary[]> {
  return (await listCooperativesPage({ pageSize: options.pageSize ?? 100, ...options })).data
}

export async function createCooperative(
  payload: CooperativeCreatePayload,
): Promise<CooperativeSummary> {
  const response = await http.post<ApiResponse<CooperativeSummary>>('/cooperatives', payload)
  return response.data.data
}

export async function updateCooperative(
  cooperativeId: string,
  payload: CooperativeUpdatePayload,
): Promise<CooperativeSummary> {
  const response = await http.patch<ApiResponse<CooperativeSummary>>(
    `/cooperatives/${cooperativeId}`,
    payload,
  )
  return response.data.data
}
