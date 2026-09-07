<script setup lang="ts">
import { reactive, ref, toRefs } from 'vue'

import { getInventoryTransaction, listInventoryTransactions } from '@/api/inventory'
import { listBatchOptions } from '@/api/batches'
import { listWarehouses } from '@/api/warehouses'
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import { usePageData } from '@/composables/usePageData'
import type { InventoryTransactionDetail } from '@/types/resources'

const filters = reactive({
  warehouseId: '',
  batchId: '',
  transactionType: '',
})

const transactionState = usePageData(
  () => listInventoryTransactions(filters),
  [],
)
const { data: items, loading, error } = toRefs(transactionState)
const { loadData } = transactionState
const warehouseState = usePageData(listWarehouses, [])
const batchState = usePageData(listBatchOptions, [])
const selectedDetail = ref<InventoryTransactionDetail | null>(null)
const detailLoading = ref(false)
const detailError = ref('')

const transactionTypes = [
  'INBOUND',
  'OUTBOUND',
  'ADJUSTMENT',
  'DAMAGE',
  'TRANSFER_OUT',
  'TRANSFER_IN',
]

async function loadDetail(transactionId: string): Promise<void> {
  detailLoading.value = true
  detailError.value = ''
  try {
    selectedDetail.value = await getInventoryTransaction(transactionId)
  } catch (reason) {
    detailError.value = reason instanceof Error ? reason.message : '流水详情加载失败'
  } finally {
    detailLoading.value = false
  }
}

function resetFilters(): void {
  filters.warehouseId = ''
  filters.batchId = ''
  filters.transactionType = ''
  void loadData()
}
</script>

<template>
  <section class="inventory-transaction-list-page">
    <PageHeader eyebrow="库存审计" title="库存流水" description="按仓库、批次和流水类型查询不可变库存流水。" />
    <PageContext />

    <form class="filter-bar inventory-transaction-list-page__filters" @submit.prevent="loadData">
      <label>
        仓库
        <select v-model="filters.warehouseId">
          <option value="">全部仓库</option>
          <option v-for="warehouse in warehouseState.data" :key="warehouse.id" :value="warehouse.id">
            {{ warehouse.name }}
          </option>
        </select>
      </label>
      <label>
        批次
        <select v-model="filters.batchId">
          <option value="">全部批次</option>
          <option v-for="batch in batchState.data" :key="batch.id" :value="batch.id">
            {{ batch.batchNo }}
          </option>
        </select>
      </label>
      <label>
        流水类型
        <select v-model="filters.transactionType">
          <option value="">全部类型</option>
          <option v-for="type in transactionTypes" :key="type" :value="type">{{ type }}</option>
        </select>
      </label>
      <div class="inventory-transaction-list-page__filter-actions">
        <button type="submit">查询</button>
        <button type="button" @click="resetFilters">重置</button>
      </div>
    </form>

    <PageState :loading="loading" :error="error" :empty="items.length === 0" @retry="loadData">
      <table class="data-table">
        <thead>
          <tr>
            <th>流水号</th>
            <th>操作单号</th>
            <th>类型</th>
            <th>数量变化</th>
            <th>发生时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td>{{ item.transactionNo }}</td>
            <td>{{ item.operationNo }}</td>
            <td>{{ item.transactionType }}</td>
            <td>{{ item.quantityDelta }}</td>
            <td>{{ item.occurredAt }}</td>
            <td>
              <button type="button" @click="loadDetail(item.id)">查看详情</button>
            </td>
          </tr>
        </tbody>
      </table>
    </PageState>

    <aside v-if="detailLoading || detailError || selectedDetail" class="inventory-transaction-list-page__detail">
      <h2>库存流水详情</h2>
      <p v-if="detailLoading">详情加载中…</p>
      <p v-else-if="detailError" role="alert">{{ detailError }}</p>
      <dl v-else-if="selectedDetail">
        <div><dt>流水号</dt><dd>{{ selectedDetail.transactionNo }}</dd></div>
        <div><dt>操作单号</dt><dd>{{ selectedDetail.operationNo }}</dd></div>
        <div><dt>流水类型</dt><dd>{{ selectedDetail.transactionType }}</dd></div>
        <div><dt>变更前</dt><dd>{{ selectedDetail.quantityBefore }}</dd></div>
        <div><dt>变更数量</dt><dd>{{ selectedDetail.quantity }}</dd></div>
        <div><dt>变更后</dt><dd>{{ selectedDetail.quantityAfter }}</dd></div>
        <div><dt>仓库</dt><dd>{{ selectedDetail.warehouseId }}</dd></div>
        <div><dt>批次</dt><dd>{{ selectedDetail.batchId }}</dd></div>
        <div><dt>发生时间</dt><dd>{{ selectedDetail.occurredAt }}</dd></div>
      </dl>
    </aside>
  </section>
</template>

<style scoped>
.inventory-transaction-list-page {
  display: grid;
  gap: var(--space-5);
}

.inventory-transaction-list-page > .page-state {
  overflow-x: auto;
}

.inventory-transaction-list-page > .page-state table {
  min-width: 48rem;
}

.inventory-transaction-list-page__filter-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.inventory-transaction-list-page__filter-actions button:last-child {
  border-color: var(--color-border-strong);
  background: transparent;
  color: var(--color-text-secondary);
}

.inventory-transaction-list-page__detail {
  display: grid;
  gap: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.inventory-transaction-list-page__detail h2 {
  margin-bottom: var(--space-4);
  font-size: var(--font-size-lg);
}

.inventory-transaction-list-page__detail dl {
  display: grid;
  gap: var(--space-2);
  margin: 0;
}

.inventory-transaction-list-page__detail dl > div {
  display: grid;
  grid-template-columns: minmax(6rem, 0.35fr) minmax(0, 1fr);
  gap: var(--space-4);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: var(--space-2);
}

.inventory-transaction-list-page__detail dt {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.inventory-transaction-list-page__detail dd {
  min-width: 0;
  margin: 0;
  color: var(--color-text-secondary);
  overflow-wrap: anywhere;
}

@media (max-width: 48rem) {
  .inventory-transaction-list-page__detail dl > div {
    grid-template-columns: 1fr;
    gap: var(--space-1);
  }
}
</style>
