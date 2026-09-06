import { beforeEach, describe, expect, it, vi } from 'vitest'

import http from './http'
import { getModelVersion, listModelVersions } from './forecasting'

vi.mock('./http', () => ({
  default: { get: vi.fn() },
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
})
