import { beforeEach, describe, expect, it, vi } from 'vitest'

import http from './http'
import {
  activateModel,
  getModelVersion,
  listModelVersions,
  submitForecastTask,
  submitModelTrainingTask,
} from './forecasting'

vi.mock('./http', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}))

describe('forecasting api', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('lists model versions', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({ data: { data: [] } })

    await expect(listModelVersions()).resolves.toEqual([])
    expect(http.get).toHaveBeenCalledWith('/model-versions', {
      params: { page: 1, pageSize: 100 },
    })
  })

  it('gets a model version detail', async () => {
    const model = {
      id: 'model-1',
      version: 'xgb-v1',
      modelType: 'XGBOOST',
      isActive: true,
      metrics: { rmse: 1.2 },
    }
    vi.mocked(http.get).mockResolvedValueOnce({ data: { data: model } })

    await expect(getModelVersion('model-1')).resolves.toEqual(model)
    expect(http.get).toHaveBeenCalledWith('/model-versions/model-1')
  })

  it('activates a model version', async () => {
    vi.mocked(http.post).mockResolvedValueOnce({
      data: { data: { id: 'model-1', isActive: true } },
    })

    await expect(activateModel('model-1')).resolves.toMatchObject({
      id: 'model-1',
      isActive: true,
    })
    expect(http.post).toHaveBeenCalledWith('/model-activations', {
      modelVersionId: 'model-1',
    })
  })

  it('submits a model training task', async () => {
    const payload = {
      modelType: 'XGBOOST' as const,
      scope: { warehouseId: 'warehouse-1', productId: 'product-1' },
      trainingRange: { startDate: '2026-01-01', endDate: '2026-08-31' },
      testRatio: 0.2,
      randomSeed: 42,
      parameters: {},
    }
    vi.mocked(http.post).mockResolvedValueOnce({
      data: { data: { id: 'task-1', taskType: 'MODEL_TRAINING', status: 'PENDING', progress: 0 } },
    })

    await expect(submitModelTrainingTask(payload)).resolves.toMatchObject({
      id: 'task-1',
      status: 'PENDING',
    })
    expect(http.post).toHaveBeenCalledWith('/model-training-tasks', payload)
  })

  it('submits a demand forecast task', async () => {
    const payload = {
      warehouseId: 'warehouse-1',
      productId: 'product-1',
      horizon: 'SEVEN_DAYS' as const,
    }
    vi.mocked(http.post).mockResolvedValueOnce({
      data: { data: { id: 'task-2', taskType: 'FORECAST', status: 'PENDING', progress: 0 } },
    })

    await expect(submitForecastTask(payload)).resolves.toMatchObject({
      id: 'task-2',
      status: 'PENDING',
    })
    expect(http.post).toHaveBeenCalledWith('/forecast-tasks', payload)
  })
})
