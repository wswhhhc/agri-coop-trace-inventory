import type { ApiResponse, ListResponse } from '@/types/api'
import type { QualityInspectionSummary } from '@/types/resources'

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

export async function listQualityInspections(
  batchId: string,
): Promise<QualityInspectionSummary[]> {
  const response = await http.get<ListResponse<QualityInspectionSummary>>(
    `/batches/${batchId}/quality-inspections`,
    { params: { page: 1, pageSize: 10 } },
  )
  return response.data.data
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
