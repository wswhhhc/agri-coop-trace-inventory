import { beforeEach, describe, expect, it, vi } from 'vitest'

import http from './http'
import { getPublicTrace } from './public-traceability'

vi.mock('./http', () => ({
  default: { get: vi.fn() },
}))

describe('public traceability api', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('loads a public trace by trace code', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({
      data: {
        data: {
          traceCode: 'tr_ABC123',
          product: { name: '苹果', categoryName: '水果', unit: 'KG', description: null },
          batch: {
            batchNo: 'APPLE-001',
            origin: '山东',
            productionDate: '2026-09-06',
            expiryDate: '2026-10-06',
            status: 'IN_STOCK',
          },
          latestInspection: null,
          timeline: [],
          dataNotice: '演示数据',
          updatedAt: '2026-09-06T10:00:00+08:00',
        },
      },
    })

    await expect(getPublicTrace('tr_ABC123')).resolves.toMatchObject({
      traceCode: 'tr_ABC123',
      batch: { batchNo: 'APPLE-001' },
    })
    expect(http.get).toHaveBeenCalledWith('/public/traces/tr_ABC123')
  })
})
