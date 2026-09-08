import { createApp, nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  createInventoryIssue,
  createInventoryLoss,
  createInventoryReceipt,
  createStocktake,
  createStockTransfer,
  listInventoryPage,
} from '@/api/inventory'
import { listBatchOptions } from '@/api/batches'
import { listProductOptions } from '@/api/products'
import { listWarehouses } from '@/api/warehouses'

import InventoryListView from './InventoryListView.vue'

vi.mock('@/api/inventory', () => ({
  createInventoryIssue: vi.fn(),
  createInventoryLoss: vi.fn(),
  createInventoryReceipt: vi.fn(),
  createStocktake: vi.fn(),
  createStockTransfer: vi.fn(),
  listInventoryPage: vi.fn(),
}))

vi.mock('@/api/batches', () => ({
  listBatchOptions: vi.fn(),
}))

vi.mock('@/api/products', () => ({
  listProductOptions: vi.fn(),
}))

vi.mock('@/api/warehouses', () => ({
  listWarehouses: vi.fn(),
}))

vi.mock('@/stores/auth', () => ({
  useAuthStore: () => ({
    hasPermission: (permission: string) => permission === 'inventory:write',
  }),
}))

async function flushPromises(): Promise<void> {
  await Promise.resolve()
  await nextTick()
  await Promise.resolve()
  await nextTick()
}

describe('InventoryListView', () => {
  beforeEach(() => {
    vi.mocked(listInventoryPage).mockResolvedValue({
      data: [],
      pagination: { page: 1, pageSize: 10, totalItems: 0, totalPages: 0 },
    })
    vi.mocked(listWarehouses).mockResolvedValue([])
    vi.mocked(listBatchOptions).mockResolvedValue([])
    vi.mocked(listProductOptions).mockResolvedValue([])
    vi.mocked(createInventoryReceipt).mockResolvedValue({ quantityAfter: 0, transactionId: 'tx-1' })
    vi.mocked(createInventoryIssue).mockResolvedValue({ quantityAfter: 0, transactionId: 'tx-2' })
    vi.mocked(createStocktake).mockResolvedValue({
      bookQuantity: 0,
      countedQuantity: 0,
      differenceQuantity: 0,
      transactionId: 'tx-3',
    })
    vi.mocked(createInventoryLoss).mockResolvedValue({ quantityAfter: 0, transactionId: 'tx-4' })
    vi.mocked(createStockTransfer).mockResolvedValue({
      transferId: 'transfer-1',
      outTransactionId: 'tx-5',
      inTransactionId: 'tx-6',
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
    document.body.innerHTML = ''
  })

  it('opens each inventory operation in a modal', async () => {
    const root = document.createElement('div')
    document.body.append(root)
    const app = createApp(InventoryListView)
    app.mount(root)

    await flushPromises()

    for (const operation of ['入库', '出库', '盘点', '报损', '仓库调拨']) {
      const button = Array.from(root.querySelectorAll('button')).find(
        (item) => item.textContent?.trim() === operation,
      )
      expect(button).not.toBeUndefined()

      button?.click()
      await nextTick()

      const dialog = document.body.querySelector('[role="dialog"]')
      expect(dialog).not.toBeNull()
      expect(dialog?.textContent).toContain(operation)
      expect(dialog?.querySelector('form')).not.toBeNull()

      const cancelButton = Array.from(dialog?.querySelectorAll('button') ?? []).find(
        (item) => item.textContent?.trim() === '取消',
      )
      cancelButton?.click()
      await nextTick()
      expect(document.body.querySelector('[role="dialog"]')).toBeNull()
    }

    app.unmount()
  })

  it('requires explicit confirmation before submitting an inventory operation', async () => {
    const root = document.createElement('div')
    document.body.append(root)
    const app = createApp(InventoryListView)
    app.mount(root)

    await flushPromises()

    const operationButton = Array.from(root.querySelectorAll('button')).find(
      (item) => item.textContent?.trim() === '入库',
    )
    operationButton?.click()
    await nextTick()

    const operationForm = document.body.querySelector('form.create-form-modal')
    operationForm?.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
    await nextTick()

    expect(createInventoryReceipt).not.toHaveBeenCalled()
    expect(document.body.querySelector('.confirm-dialog')?.textContent).toContain('确认提交')

    const cancelButton = document.body.querySelector('.confirm-dialog button')
    cancelButton?.click()
    await nextTick()
    expect(createInventoryReceipt).not.toHaveBeenCalled()
    expect(document.body.querySelector('.confirm-dialog')).toBeNull()

    operationForm?.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
    await nextTick()
    const confirmButton = document.body.querySelector('.confirm-dialog button:last-child')
    confirmButton?.click()
    await flushPromises()

    expect(createInventoryReceipt).toHaveBeenCalledOnce()
    app.unmount()
  })

  it('opens the confirmation dialog for every inventory operation', async () => {
    const root = document.createElement('div')
    document.body.append(root)
    const app = createApp(InventoryListView)
    app.mount(root)

    await flushPromises()

    for (const operation of ['入库', '出库', '盘点', '报损', '仓库调拨']) {
      const operationButton = Array.from(root.querySelectorAll('button')).find(
        (item) => item.textContent?.trim() === operation,
      )
      operationButton?.click()
      await nextTick()

      const operationForm = document.body.querySelector('form.create-form-modal')
      operationForm?.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
      await nextTick()

      expect(document.body.querySelector('.confirm-dialog')?.textContent).toContain(`确认提交${operation}`)
      document.body.querySelector('.confirm-dialog button')?.click()
      await nextTick()
      expect(document.body.querySelector('.confirm-dialog')).toBeNull()
      document.body.querySelector('.modal-shell__close')?.dispatchEvent(new Event('click', { bubbles: true }))
      await nextTick()
    }

    app.unmount()
  })
})
