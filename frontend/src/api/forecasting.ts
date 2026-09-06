import type { ApiResponse, ListResponse } from '@/types/api'
import type { ForecastSummary, ModelVersionSummary, TaskSummary } from '@/types/resources'

import http from './http'

export interface ModelTrainingTaskPayload {
  modelType: 'XGBOOST'
  scope: { warehouseId: string; productId: string }
  trainingRange: { startDate: string; endDate: string }
  testRatio: number
  randomSeed: number
  parameters: Record<string, unknown>
}

export async function listForecastResults(): Promise<ForecastSummary[]> {
  const response = await http.get<ListResponse<ForecastSummary>>('/forecast-results', {
    params: { page: 1, pageSize: 20 },
  })
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

export async function getForecastingTask(taskId: string): Promise<TaskSummary> {
  const response = await http.get<ApiResponse<TaskSummary>>(`/tasks/${taskId}`)
  return response.data.data
}
