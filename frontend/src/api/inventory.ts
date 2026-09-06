import type { ListResponse } from '@/types/api'
import type { InventorySummary, InventoryTransactionSummary } from '@/types/resources'

import http from './http'

export async function listInventory(): Promise<InventorySummary[]> {
  const response = await http.get<ListResponse<InventorySummary>>('/inventories', {
    params: { page: 1, pageSize: 20 },
  })
  return response.data.data
}

export async function listInventoryTransactions(): Promise<InventoryTransactionSummary[]> {
  const response = await http.get<ListResponse<InventoryTransactionSummary>>(
    '/inventory-transactions',
    { params: { page: 1, pageSize: 20 } },
  )
  return response.data.data
}
