import type { ApiResponse, ListResponse } from '@/types/api'
import type { QualityInspectionSummary } from '@/types/resources'
import { cleanQueryParams } from '@/composables/usePageData'

import http from './http'

export type InspectionConclusion = 'PENDING' | 'PASSED' | 'FAILED'

export interface QualityInspectionItemCreatePayload {
  name: string
  value: string
  unit: string | null
  standard: string
  isQualified: boolean
}

export interface QualityInspectionCreatePayload {
  inspectionDate: string
  conclusion: InspectionConclusion
  items: QualityInspectionItemCreatePayload[]
  remarks: string | null
  attachmentFileIds?: string[]
}

export interface QualityInspectionListParams {
  page?: number
  pageSize?: number
  conclusion?: InspectionConclusion
}

export async function listQualityInspectionsPage(
  batchId: string,
  options: QualityInspectionListParams = {},
): Promise<ListResponse<QualityInspectionSummary>> {
  const params = cleanQueryParams({
    page: options.page ?? 1,
    pageSize: options.pageSize ?? 10,
    conclusion: options.conclusion,
  })
  const response = await http.get<ListResponse<QualityInspectionSummary>>(
    `/batches/${batchId}/quality-inspections`,
    { params },
  )
  return response.data
}

export async function listQualityInspections(
  batchId: string,
): Promise<QualityInspectionSummary[]> {
  return (await listQualityInspectionsPage(batchId)).data
}

export async function createQualityInspection(
  batchId: string,
  payload: QualityInspectionCreatePayload,
): Promise<QualityInspectionSummary> {
  const response = await http.post<ApiResponse<QualityInspectionSummary>>(
    `/batches/${batchId}/quality-inspections`,
    payload,
  )
  return response.data.data
}
