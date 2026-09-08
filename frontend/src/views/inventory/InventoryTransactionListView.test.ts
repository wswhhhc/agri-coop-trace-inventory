import { createApp, nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  getInventoryTransaction,
  listInventoryTransactionsPage,
} from '@/api/inventory'
import { listBatchOptions } from '@/api/batches'
import { listWarehouses } from '@/api/warehouses'

import InventoryTransactionListView from './InventoryTransactionListView.vue'

vi.mock('@/api/inventory', () => ({
  getInventoryTransaction: vi.fn(),
  listInventoryTransactionsPage: vi.fn(),
}))

vi.mock('@/api/batches', () => ({
  listBatchOptions: vi.fn(),
}))

vi.mock('@/api/warehouses', () => ({
  listWarehouses: vi.fn(),
}))

const transaction = {
  id: 'transaction-1',
  transactionNo: 'TX-001',
  operationNo: 'OP-001',
  transactionType: 'INBOUND',
  quantity: 10,
  quantityDelta: 10,
  warehouseId: 'warehouse-1',
  batchId: 'batch-1',
  occurredAt: '2026-09-08T10:00:00Z',
}

const transactionDetail = {
  ...transaction,
  transactionId: 'transaction-1',
  operationId: 'operation-1',
  quantityBefore: 0,
  quantityAfter: 10,
}

async function flushPromises(): Promise<void> {
  await Promise.resolve()
  await nextTick()
  await Promise.resolve()
  await nextTick()
}

describe('InventoryTransactionListView', () => {
  beforeEach(() => {
    vi.mocked(listInventoryTransactionsPage).mockResolvedValue({
      data: [transaction],
      pagination: { page: 1, pageSize: 10, totalItems: 1, totalPages: 1 },
    })
    vi.mocked(listBatchOptions).mockResolvedValue([])
    vi.mocked(listWarehouses).mockResolvedValue([])
    vi.mocked(getInventoryTransaction).mockResolvedValue(transactionDetail)
  })

  afterEach(() => {
    vi.restoreAllMocks()
    document.body.innerHTML = ''
  })

  it('opens transaction details in a modal instead of appending them below the table', async () => {
    const root = document.createElement('div')
    document.body.append(root)
    const app = createApp(InventoryTransactionListView)
    app.mount(root)

    await flushPromises()
    const detailButton = Array.from(root.querySelectorAll('button')).find(
      (button) => button.textContent?.trim() === '查看详情',
    )
    expect(detailButton).not.toBeUndefined()

    detailButton?.click()
    await flushPromises()

    const dialog = document.body.querySelector('[role="dialog"]')
    expect(dialog).not.toBeNull()
    expect(dialog?.textContent).toContain('库存流水详情')
    expect(root.querySelector('[role="dialog"]')).toBeNull()
    expect(root.querySelector('.inventory-transaction-list-page__detail')).toBeNull()

    app.unmount()
  })
})
