import { beforeEach, describe, expect, it, vi } from 'vitest'

import http from './http'
import { createInventoryIssue, createInventoryReceipt } from './inventory'

vi.mock('./http', () => ({
  default: { post: vi.fn() },
}))

describe('inventory api', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('creates a receipt with a reusable idempotency key', async () => {
    const payload = {
      warehouseId: 'warehouse-1',
      batchId: 'batch-1',
      quantity: 125,
      occurredAt: '2026-09-06T10:00:00.000Z',
      referenceNo: 'IN-001',
      remark: null,
    }
    vi.mocked(http.post).mockResolvedValueOnce({
      data: { data: { transactionId: 'transaction-1', quantityAfter: 125 } },
    })

    await expect(createInventoryReceipt(payload, 'idempotency-1')).resolves.toEqual({
      transactionId: 'transaction-1',
      quantityAfter: 125,
    })
    expect(http.post).toHaveBeenCalledWith('/inventory-receipts', payload, {
      headers: { 'Idempotency-Key': 'idempotency-1' },
    })
  })

  it('creates an issue with a reusable idempotency key', async () => {
    const payload = {
      warehouseId: 'warehouse-1',
      batchId: 'batch-1',
      quantity: 10,
      occurredAt: '2026-09-06T11:00:00.000Z',
      referenceNo: 'OUT-001',
      destination: '配送中心',
      remark: null,
    }
    vi.mocked(http.post).mockResolvedValueOnce({
      data: { data: { transactionId: 'transaction-2', quantityAfter: 115 } },
    })

    await expect(createInventoryIssue(payload, 'idempotency-2')).resolves.toEqual({
      transactionId: 'transaction-2',
      quantityAfter: 115,
    })
    expect(http.post).toHaveBeenCalledWith('/inventory-issues', payload, {
      headers: { 'Idempotency-Key': 'idempotency-2' },
    })
  })
})
