import { beforeEach, describe, expect, it, vi } from 'vitest'

import http from './http'
import {
  getAlertDistribution,
  getDashboardSummary,
  getInventoryTrends,
  getProductRanking,
} from './dashboard'

vi.mock('./http', () => ({
  default: { get: vi.fn() },
}))

describe('dashboard api', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(http.get).mockResolvedValue({ data: { data: [] } })
  })

  it('uses the dashboard paths and converts query options to URL parameters', async () => {
    const params = { warehouseId: 'warehouse-1', startDate: '2026-08-01', endDate: '2026-08-30' }

    await getDashboardSummary(params)
    await getInventoryTrends(params)
    await getAlertDistribution(params)
    await getProductRanking({ ...params, limit: 10 })

    expect(http.get).toHaveBeenNthCalledWith(1, '/dashboard/summary', { params })
    expect(http.get).toHaveBeenNthCalledWith(2, '/dashboard/inventory-trends', { params })
    expect(http.get).toHaveBeenNthCalledWith(3, '/dashboard/alert-distribution', { params })
    expect(http.get).toHaveBeenNthCalledWith(4, '/dashboard/product-ranking', { params: { ...params, limit: 10 } })
    expect(JSON.stringify(http.get.mock.calls)).not.toContain('cooperativeId')
  })

  it('omits undefined options instead of sending empty URL parameters', async () => {
    await getProductRanking({ limit: 10 })

    expect(http.get).toHaveBeenCalledWith('/dashboard/product-ranking', { params: { limit: 10 } })
  })
})
