import { beforeEach, describe, expect, it, vi } from 'vitest'

import http from './http'
import {
  getAlertDistribution,
  getDashboardSummary,
  getForecastComparison,
  getInventoryTrends,
  getProductRanking,
  listInventoryTrendsPage,
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
    await getForecastComparison(params)

    expect(http.get).toHaveBeenNthCalledWith(1, '/dashboard/summary', { params })
    expect(http.get).toHaveBeenNthCalledWith(2, '/dashboard/inventory-trends', {
      params: { page: 1, pageSize: 20, ...params },
    })
    expect(http.get).toHaveBeenNthCalledWith(3, '/dashboard/alert-distribution', { params })
    expect(http.get).toHaveBeenNthCalledWith(4, '/dashboard/product-ranking', { params: { ...params, limit: 10 } })
    expect(http.get).toHaveBeenNthCalledWith(5, '/dashboard/forecast-comparison', { params })
    expect(JSON.stringify(http.get.mock.calls)).not.toContain('cooperativeId')
  })

  it('requests a paginated inventory trend page with dashboard filters', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({
      data: {
        data: [],
        pagination: { page: 2, pageSize: 10, totalItems: 21, totalPages: 3 },
      },
    })

    await expect(
      listInventoryTrendsPage({
        page: 2,
        pageSize: 10,
        warehouseId: 'warehouse-1',
        startDate: '2026-08-01',
        endDate: '2026-08-30',
      }),
    ).resolves.toEqual({
      data: [],
      pagination: { page: 2, pageSize: 10, totalItems: 21, totalPages: 3 },
    })

    expect(http.get).toHaveBeenCalledWith('/dashboard/inventory-trends', {
      params: {
        page: 2,
        pageSize: 10,
        warehouseId: 'warehouse-1',
        startDate: '2026-08-01',
        endDate: '2026-08-30',
      },
    })
  })

  it('omits undefined options instead of sending empty URL parameters', async () => {
    await getProductRanking({ limit: 10 })

    expect(http.get).toHaveBeenCalledWith('/dashboard/product-ranking', { params: { limit: 10 } })
  })
})
