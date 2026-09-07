import type { ApiResponse, ListResponse } from '@/types/api'
import type {
  ForecastResultDetailSummary,
  ModelVersionSummary,
  TaskSummary,
} from '@/types/resources'

import http from './http'

export interface ModelTrainingTaskPayload {
  modelType: 'XGBOOST'
  scope: { warehouseId: string; productId: string }
  trainingRange: { startDate: string; endDate: string }
  testRatio: number
  randomSeed: number
  parameters: Record<string, unknown>
}

export interface ForecastTaskPayload {
  warehouseId: string
  productId: string
  horizon: 'SEVEN_DAYS' | 'THIRTY_DAYS'
  modelVersionId?: string
}

export async function listForecastResults(): Promise<ForecastResultDetailSummary[]> {
  const response = await listForecastResultsPage()
  return response.data.data
}

export interface ForecastResultListParams {
  page?: number
  pageSize?: number
}

export async function listForecastResultsPage(
  options: ForecastResultListParams = {},
): Promise<ListResponse<ForecastResultDetailSummary>> {
  const response = await http.get<ListResponse<ForecastResultDetailSummary>>('/forecast-results', {
    params: { page: options.page ?? 1, pageSize: options.pageSize ?? 20 },
  })
  return response.data
}

export async function getForecastResult(
  forecastResultId: string,
): Promise<ForecastResultDetailSummary> {
  const response = await http.get<ApiResponse<ForecastResultDetailSummary>>(
    `/forecast-results/${forecastResultId}`,
  )
  return response.data.data
}

export async function listModelVersions(): Promise<ModelVersionSummary[]> {
  const response = await http.get<ListResponse<ModelVersionSummary>>('/model-versions', {
    params: { page: 1, pageSize: 100 },
  })
  return response.data.data
}

export async function getModelVersion(modelVersionId: string): Promise<ModelVersionSummary> {
  const response = await http.get<ApiResponse<ModelVersionSummary>>(
    `/model-versions/${modelVersionId}`,
  )
  return response.data.data
}

export async function activateModel(modelVersionId: string): Promise<ModelVersionSummary> {
  const response = await http.post<ApiResponse<ModelVersionSummary>>('/model-activations', {
    modelVersionId,
  })
  return response.data.data
}

export async function submitModelTrainingTask(
  payload: ModelTrainingTaskPayload,
): Promise<TaskSummary> {
  const response = await http.post<ApiResponse<TaskSummary>>('/model-training-tasks', payload)
  return response.data.data
}

export async function submitForecastTask(payload: ForecastTaskPayload): Promise<TaskSummary> {
  const response = await http.post<ApiResponse<TaskSummary>>('/forecast-tasks', payload)
  return response.data.data
}

export async function getForecastingTask(taskId: string): Promise<TaskSummary> {
  const response = await http.get<ApiResponse<TaskSummary>>(`/tasks/${taskId}`)
  return response.data.data
}
