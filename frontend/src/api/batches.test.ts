import { beforeEach, describe, expect, it, vi } from 'vitest'

import http from './http'
import { createBatch, getBatch, listBatchOptions, listBatches, updateBatch } from './batches'

vi.mock('./http', () => ({
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn() },
}))

describe('batches api', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('loads a paginated batch list', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({
      data: {
        data: [{ id: 'batch-1' }],
        pagination: { page: 2, pageSize: 10, totalItems: 11, totalPages: 2 },
      },
    })

    await expect(listBatches({ page: 2, pageSize: 10 })).resolves.toEqual({
      data: [{ id: 'batch-1' }],
      pagination: { page: 2, pageSize: 10, totalItems: 11, totalPages: 2 },
    })
    expect(http.get).toHaveBeenCalledWith('/batches', {
      params: { page: 2, pageSize: 10 },
    })
  })

  it('sends supported batch filters and removes empty filters', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({ data: { data: [] } })

    await listBatches({
      keyword: '苹果',
      productId: 'product-1',
      warehouseId: 'warehouse-1',
      status: 'IN_STOCK',
      productionDateFrom: '2026-01-01',
      productionDateTo: '2026-01-31',
    })

    expect(http.get).toHaveBeenCalledWith('/batches', {
      params: {
        page: 1,
        pageSize: 10,
        keyword: '苹果',
        productId: 'product-1',
        warehouseId: 'warehouse-1',
        status: 'IN_STOCK',
        productionDateFrom: '2026-01-01',
        productionDateTo: '2026-01-31',
      },
    })
  })

  it('loads all batches for option selectors by default', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({ data: { data: [], pagination: { page: 1, pageSize: 100, totalItems: 0, totalPages: 0 } } })

    await expect(listBatchOptions()).resolves.toEqual([])
    expect(http.get).toHaveBeenCalledWith('/batches', {
      params: { page: 1, pageSize: 100 },
    })
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

  it('loads a batch detail by id', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({
      data: {
        data: {
          id: 'batch-1',
          productId: 'product-1',
          batchNo: 'APPLE-20260906-001',
          traceCode: 'tr_ABC123',
          origin: '山东',
          productionDate: '2026-09-06',
          expiryDate: '2026-10-06',
          responsiblePerson: null,
          status: 'CREATED',
        },
      },
    })

    await expect(getBatch('batch-1')).resolves.toMatchObject({
      id: 'batch-1',
      batchNo: 'APPLE-20260906-001',
    })
    expect(http.get).toHaveBeenCalledWith('/batches/batch-1')
  })

  it('updates editable batch fields and status', async () => {
    vi.mocked(http.patch).mockResolvedValueOnce({
      data: {
        data: {
          id: 'batch-1',
          productId: 'product-1',
          batchNo: 'APPLE-20260906-001',
          traceCode: 'tr_ABC123',
          origin: '山东青岛',
          productionDate: '2026-09-06',
          expiryDate: '2026-10-10',
          responsiblePerson: '李四',
          status: 'IN_STOCK',
        },
      },
    })

    const payload = {
      origin: '山东青岛',
      expiryDate: '2026-10-10',
      responsiblePerson: '李四',
      status: 'IN_STOCK' as const,
    }

    await expect(updateBatch('batch-1', payload)).resolves.toMatchObject({
      origin: '山东青岛',
      status: 'IN_STOCK',
    })
    expect(http.patch).toHaveBeenCalledWith('/batches/batch-1', payload)
  })
})
