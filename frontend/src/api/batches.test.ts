import { beforeEach, describe, expect, it, vi } from 'vitest'

import http from './http'
import { createBatch } from './batches'

vi.mock('./http', () => ({
  default: { post: vi.fn() },
}))

describe('batches api', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('creates a batch without fabricating the trace code', async () => {
    vi.mocked(http.post).mockResolvedValueOnce({
      data: {
        data: {
          id: 'batch-1',
          productId: 'product-1',
          batchNo: 'APPLE-20260906-001',
          traceCode: 'tr_ABC123',
          origin: '山东',
          productionDate: '2026-09-06',
          expiryDate: '2026-10-06',
          responsiblePerson: '张三',
          status: 'CREATED',
        },
      },
    })

    const payload = {
      productId: 'product-1',
      batchNo: 'APPLE-20260906-001',
      origin: '山东',
      productionDate: '2026-09-06',
      expiryDate: '2026-10-06',
      responsiblePerson: '张三',
    }

    await expect(createBatch(payload)).resolves.toMatchObject({
      id: 'batch-1',
      traceCode: 'tr_ABC123',
    })
    expect(http.post).toHaveBeenCalledWith('/batches', payload)
  })
})
