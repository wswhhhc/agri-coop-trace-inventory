import { createApp, defineComponent, h } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  getAlertDistribution,
  getDashboardSummary,
  getInventoryTrends,
  getProductRanking,
} from '@/api/dashboard'

import { useDashboard } from './useDashboard'

vi.mock('@/api/dashboard', () => ({
  getAlertDistribution: vi.fn(),
  getDashboardSummary: vi.fn(),
  getInventoryTrends: vi.fn(),
  getProductRanking: vi.fn(),
}))

describe('useDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(getDashboardSummary).mockResolvedValue({
      productCount: 1,
      batchCount: 2,
      inventoryByUnit: [{ unit: 'kg', quantity: 10 }],
      pendingAlertCount: 0,
      expiringBatchCount: 0,
      lowStockProductCount: 0,
      updatedAt: '2026-09-06T00:00:00Z',
    })
    vi.mocked(getInventoryTrends).mockResolvedValue([])
    vi.mocked(getAlertDistribution).mockResolvedValue({ totalCount: 0, items: [] })
    vi.mocked(getProductRanking).mockResolvedValue([])
  })

  it('keeps other modules available and retries only the failed module', async () => {
    vi.mocked(getInventoryTrends)
      .mockRejectedValueOnce(new Error('temporary failure'))
      .mockResolvedValueOnce([
        {
          date: '2026-09-06',
          unit: 'kg',
          inboundQuantity: 20,
          outboundQuantity: 5,
          endingQuantity: 15,
        },
      ])

    let dashboard: ReturnType<typeof useDashboard> | undefined
    const app = createApp(
      defineComponent({
        setup() {
          dashboard = useDashboard()
          return () => h('div')
        },
      }),
    )
    app.mount(document.createElement('div'))

    await vi.waitFor(() => expect(dashboard?.errors.inventoryTrends).toBe('请求失败，请稍后重试'))
    expect(dashboard?.summary.value?.productCount).toBe(1)

    await dashboard?.retry('inventoryTrends')

    expect(dashboard?.errors.inventoryTrends).toBe('')
    expect(dashboard?.inventoryTrends.value).toHaveLength(1)
    expect(getDashboardSummary).toHaveBeenCalledOnce()
    expect(getInventoryTrends).toHaveBeenCalledTimes(2)

    app.unmount()
  })
})
