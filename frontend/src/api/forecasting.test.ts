import { beforeEach, describe, expect, it, vi } from 'vitest'

import http from './http'
import { activateModel, getModelVersion, listModelVersions } from './forecasting'

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
})
