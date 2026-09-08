import { beforeEach, describe, expect, it, vi } from 'vitest'

import http from './http'
import {
  createInventoryIssue,
  createInventoryLoss,
  createInventoryReceipt,
  createStocktake,
  createStockTransfer,
  getInventoryTransaction,
  listInventory,
  listInventoryTransactions,
} from './inventory'

vi.mock('./http', () => ({
  default: { get: vi.fn(), post: vi.fn() },
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

  it('creates a stocktake with a counted quantity and reason', async () => {
    const payload = {
      warehouseId: 'warehouse-1',
      batchId: 'batch-1',
      countedQuantity: 110,
      occurredAt: '2026-09-06T12:00:00.000Z',
      reason: '月度盘点',
      remark: null,
    }
    vi.mocked(http.post).mockResolvedValueOnce({
      data: { data: { transactionId: 'transaction-3', bookQuantity: 115, countedQuantity: 110, differenceQuantity: -5 } },
    })

    await expect(createStocktake(payload, 'idempotency-3')).resolves.toEqual({
      transactionId: 'transaction-3',
      bookQuantity: 115,
      countedQuantity: 110,
      differenceQuantity: -5,
    })
    expect(http.post).toHaveBeenCalledWith('/stocktakes', payload, {
      headers: { 'Idempotency-Key': 'idempotency-3' },
    })
  })

  it('creates an inventory loss with a required reason', async () => {
    const payload = {
      warehouseId: 'warehouse-1',
      batchId: 'batch-1',
      quantity: 5,
      occurredAt: '2026-09-06T13:00:00.000Z',
      reason: '运输破损',
      remark: null,
    }
    vi.mocked(http.post).mockResolvedValueOnce({
      data: { data: { transactionId: 'transaction-4', quantityAfter: 105 } },
    })

    await expect(createInventoryLoss(payload, 'idempotency-4')).resolves.toEqual({
      transactionId: 'transaction-4',
      quantityAfter: 105,
    })
    expect(http.post).toHaveBeenCalledWith('/inventory-losses', payload, {
      headers: { 'Idempotency-Key': 'idempotency-4' },
    })
  })

  it('creates a stock transfer between two warehouses', async () => {
    const payload = {
      sourceWarehouseId: 'warehouse-1',
      targetWarehouseId: 'warehouse-2',
      batchId: 'batch-1',
      quantity: 20,
      occurredAt: '2026-09-06T14:00:00.000Z',
      remark: '调拨补货',
    }
    vi.mocked(http.post).mockResolvedValueOnce({
      data: { data: { transferId: 'transfer-1', outTransactionId: 'transaction-5', inTransactionId: 'transaction-6' } },
    })

    await expect(createStockTransfer(payload, 'idempotency-5')).resolves.toEqual({
      transferId: 'transfer-1',
      outTransactionId: 'transaction-5',
      inTransactionId: 'transaction-6',
    })
    expect(http.post).toHaveBeenCalledWith('/stock-transfers', payload, {
      headers: { 'Idempotency-Key': 'idempotency-5' },
    })
  })

  it('lists transactions with warehouse and type filters', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({ data: { data: [] } })

    await expect(listInventoryTransactions({
      warehouseId: 'warehouse-1',
      batchId: 'batch-1',
      transactionType: 'OUTBOUND',
    })).resolves.toEqual([])
    expect(http.get).toHaveBeenCalledWith('/inventory-transactions', {
      params: {
        page: 1,
        pageSize: 10,
        warehouseId: 'warehouse-1',
        batchId: 'batch-1',
        transactionType: 'OUTBOUND',
      },
    })
  })

  it('lists current inventory with warehouse, product, batch, risk, and keyword filters', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({ data: { data: [], pagination: { page: 2, pageSize: 20, totalItems: 0, totalPages: 0 } } })

    await expect(listInventory({
      page: 2,
      pageSize: 20,
      warehouseId: 'warehouse-1',
      productId: 'product-1',
      batchId: 'batch-1',
      stockRisk: 'LOW_STOCK',
      keyword: '  玉米  ',
    })).resolves.toEqual([])
    expect(http.get).toHaveBeenCalledWith('/inventories', {
      params: {
        page: 2,
        pageSize: 20,
        warehouseId: 'warehouse-1',
        productId: 'product-1',
        batchId: 'batch-1',
        stockRisk: 'LOW_STOCK',
        keyword: '玉米',
      },
    })
  })

  it('gets a transaction detail', async () => {
    const detail = {
      id: 'transaction-1',
      transactionId: 'transaction-1',
      transactionNo: 'TRX-001',
      operationNo: 'OP-001',
      operationId: 'operation-1',
      transactionType: 'INBOUND',
      quantity: 125,
      quantityDelta: 125,
      quantityBefore: 0,
      quantityAfter: 125,
      warehouseId: 'warehouse-1',
      batchId: 'batch-1',
      occurredAt: '2026-09-06T10:00:00.000Z',
    }
    vi.mocked(http.get).mockResolvedValueOnce({ data: { data: detail } })

    await expect(getInventoryTransaction('transaction-1')).resolves.toEqual(detail)
    expect(http.get).toHaveBeenCalledWith('/inventory-transactions/transaction-1')
  })
})
