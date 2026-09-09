import { createApp, nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { createWarehouse, listWarehousesPage } from '@/api/warehouses'
import { listUsers } from '@/api/users'

import WarehouseListView from './WarehouseListView.vue'

vi.mock('@/api/warehouses', () => ({
  createWarehouse: vi.fn(),
  listWarehousesPage: vi.fn(),
  updateWarehouse: vi.fn(),
}))

vi.mock('@/api/users', () => ({
  listUsers: vi.fn(),
}))

vi.mock('@/stores/auth', () => ({
  useAuthStore: () => ({
    role: 'COOPERATIVE_ADMIN',
    hasPermission: (permission: string) => permission === 'warehouse:manage',
  }),
}))

async function flushPromises(): Promise<void> {
  await Promise.resolve()
  await nextTick()
  await Promise.resolve()
  await nextTick()
}

describe('WarehouseListView', () => {
  beforeEach(() => {
    vi.mocked(listWarehousesPage).mockResolvedValue({
      data: [],
      pagination: { page: 1, pageSize: 10, totalItems: 0, totalPages: 0 },
    })
    vi.mocked(listUsers).mockResolvedValue([
      {
        id: 'user-1',
        username: 'zhangsan',
        displayName: '张三',
        role: 'WAREHOUSE_STAFF',
        cooperativeId: 'cooperative-1',
        warehouseIds: [],
        phone: null,
        status: 'ACTIVE',
      },
    ])
    vi.mocked(createWarehouse).mockResolvedValue({
      id: 'warehouse-1',
      cooperativeId: 'cooperative-1',
      code: 'WH-ABC123',
      name: '中心仓',
      address: null,
      managerName: '张三',
      status: 'ACTIVE',
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
    document.body.innerHTML = ''
  })

  it('uses the shared select field with existing warehouse staff as manager options', async () => {
    const root = document.createElement('div')
    document.body.append(root)
    const app = createApp(WarehouseListView)
    app.mount(root)

    await flushPromises()

    expect(listUsers).toHaveBeenCalledWith({
      pageSize: 100,
      role: 'WAREHOUSE_STAFF',
      status: 'ACTIVE',
    })

    root.querySelector<HTMLButtonElement>('.create-button')?.click()
    await nextTick()

    const dialog = document.body.querySelector('[role="dialog"]')
    expect(dialog?.querySelector('.select-field')).not.toBeNull()
    expect(dialog?.querySelector('input[name="managerName"]:not([type="hidden"])')).toBeNull()

    dialog?.querySelector<HTMLButtonElement>('.select-field__trigger')?.click()
    await nextTick()

    expect(dialog?.querySelector('.select-field__option')?.textContent).toContain('张三（zhangsan）')

    app.unmount()
  })
})
