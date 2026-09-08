<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import FilterBar from '@/components/common/FilterBar.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import PageState from '@/components/common/PageState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import GeneratedCodeField from '@/components/common/GeneratedCodeField.vue'
import CreateFormModal from '@/components/common/CreateFormModal.vue'
import SelectField, { type SelectFieldOption } from '@/components/common/SelectField.vue'
import { createBatch, listBatches, type BatchCreatePayload, type BatchListParams, type BatchStatus } from '@/api/batches'
import { listProductOptions } from '@/api/products'
import { listWarehouses } from '@/api/warehouses'
import { getPagePlaceholderCount, useFilteredPaginatedList, usePageData } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import { getApiErrorMessage } from '@/utils/api-error'
import { formatBatchStatus } from '@/utils/batch-format'

type BatchFilterState = Pick<
  BatchListParams,
  'keyword' | 'productId' | 'warehouseId' | 'status' | 'productionDateFrom' | 'productionDateTo'
> & {
  keyword: string
  productId: string
  warehouseId: string
  status: BatchStatus | ''
  productionDateFrom: string
  productionDateTo: string
}

const batchList = useFilteredPaginatedList(
  (params) => listBatches({
    ...params,
    keyword: params.keyword || undefined,
    productId: params.productId || undefined,
    warehouseId: params.warehouseId || undefined,
    status: params.status || undefined,
    productionDateFrom: params.productionDateFrom || undefined,
    productionDateTo: params.productionDateTo || undefined,
  }),
  {
    keyword: '',
    productId: '',
    warehouseId: '',
    status: '',
    productionDateFrom: '',
    productionDateTo: '',
  } satisfies BatchFilterState,
)
const placeholderCount = computed(() =>
  getPagePlaceholderCount(batchList.pagination.pageSize, batchList.items.length),
)
const productState = usePageData(
  () => listProductOptions({ isActive: true, pageSize: 100 }),
  [],
)
const filterProductState = usePageData(() => listProductOptions({ pageSize: 100 }), [])
const warehouseState = usePageData(() => listWarehouses({ pageSize: 100 }), [])
const productFilterOptions = computed<SelectFieldOption[]>(() => [
  { value: '', label: '全部产品' },
  ...filterProductState.data.map((product) => ({
    value: product.id,
    label: `${product.name}（${product.code}）`,
  })),
])
const warehouseFilterOptions = computed<SelectFieldOption[]>(() => [
  { value: '', label: '全部仓库' },
  ...warehouseState.data.map((warehouse) => ({
    value: warehouse.id,
    label: `${warehouse.name}（${warehouse.code}）`,
  })),
])
const batchStatusOptions: SelectFieldOption[] = [
  { value: '', label: '全部状态' },
  { value: 'CREATED', label: '已创建' },
  { value: 'IN_STOCK', label: '库存中' },
  { value: 'DEPLETED', label: '已耗尽' },
  { value: 'BLOCKED', label: '已冻结' },
  { value: 'EXPIRED', label: '已过期' },
]
const authStore = useAuthStore()
const canManage = computed(() => authStore.hasPermission('batch:manage'))
const canManageProducts = computed(() => authStore.hasPermission('product:manage'))
const showCreateModal = ref(false)
const submitting = ref(false)
const formError = ref('')
const successMessage = ref('')
const form = reactive<BatchCreatePayload>({
  productId: '',
  origin: '',
  productionDate: '',
  expiryDate: '',
  responsiblePerson: null,
})

function productName(productId: string): string {
  return productState.data.find((product) => product.id === productId)?.name ?? '—'
}

function batchStatusTone(value: string): 'success' | 'warning' | 'danger' | 'info' {
  if (value === 'IN_STOCK') return 'success'
  if (value === 'EXPIRED' || value === 'BLOCKED') return 'danger'
  if (value === 'DEPLETED') return 'warning'
  return 'info'
}

function resetForm(): void {
  form.productId = ''
  form.origin = ''
  form.productionDate = ''
  form.expiryDate = ''
  form.responsiblePerson = null
}

function openCreateModal(): void {
  resetForm()
  formError.value = ''
  successMessage.value = ''
  showCreateModal.value = true
}

function closeCreateModal(): void {
  if (submitting.value) return
  showCreateModal.value = false
  formError.value = ''
}

async function handleSubmit(): Promise<void> {
  submitting.value = true
  formError.value = ''
  successMessage.value = ''
  try {
    const created = await createBatch({
      productId: form.productId,
      origin: form.origin.trim(),
      productionDate: form.productionDate,
      expiryDate: form.expiryDate,
      responsiblePerson: form.responsiblePerson?.trim() || null,
    })
    resetForm()
    showCreateModal.value = false
    successMessage.value = `批次创建成功，编号为 ${created.batchNo}，追溯码为 ${created.traceCode}。`
    await batchList.loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="batch-list-page">
    <div class="page-toolbar">
      <button v-if="canManage" class="create-button" type="button" @click="openCreateModal">创建批次</button>
    </div>
    <FilterBar @submit="batchList.applyFilters" @reset="batchList.resetFilters">
      <label>
        关键字
        <input v-model="batchList.filters.keyword" placeholder="批次编号、追溯码或产地" />
      </label>
      <label>
        产品
        <SelectField v-model="batchList.filters.productId" :options="productFilterOptions" />
      </label>
      <label>
        仓库
        <SelectField v-model="batchList.filters.warehouseId" :options="warehouseFilterOptions" />
      </label>
      <label>
        状态
        <SelectField v-model="batchList.filters.status" :options="batchStatusOptions" />
      </label>
      <label>
        生产日期起
        <input v-model="batchList.filters.productionDateFrom" type="date" />
      </label>
      <label>
        生产日期止
        <input v-model="batchList.filters.productionDateTo" type="date" />
      </label>
    </FilterBar>
    <p v-if="successMessage" class="create-status" role="status">{{ successMessage }}</p>

    <CreateFormModal
      :open="showCreateModal"
      title="创建批次"
      :submitting="submitting"
      :submit-disabled="productState.loading"
      :error="formError || productState.error"
      @close="closeCreateModal"
      @submit="handleSubmit"
    >
      <label>
        产品
        <div class="field-with-action">
          <select v-model="form.productId" name="productId" required>
            <option value="" disabled>请选择产品</option>
            <option v-for="product in productState.data" :key="product.id" :value="product.id">
              {{ product.name }}（{{ product.code }}）
            </option>
          </select>
          <RouterLink class="inline-link" :to="{ name: 'products' }">
            {{ canManageProducts ? '新增产品' : '查看产品' }}
          </RouterLink>
        </div>
        <span v-if="!productState.loading && !productState.error && productState.data.length === 0" class="field-help" role="status">
          暂无启用产品，请先到产品管理中新增产品。
        </span>
      </label>
      <GeneratedCodeField label="批次编号" format="产品编码-YYYYMMDD-XXXXXX" />
      <label>
        产地
        <input v-model="form.origin" name="origin" required maxlength="255" />
      </label>
      <label>
        生产日期
        <input v-model="form.productionDate" type="date" name="productionDate" required />
      </label>
      <label>
        到期日期
        <input v-model="form.expiryDate" type="date" name="expiryDate" required />
      </label>
      <label>
        负责人
        <input v-model="form.responsiblePerson" name="responsiblePerson" maxlength="50" />
      </label>
    </CreateFormModal>
    <PageState
      :loading="batchList.loading"
      :error="batchList.error"
      :empty="batchList.items.length === 0"
      :preserve-content-on-loading="batchList.items.length > 0"
      @retry="batchList.loadData"
    >
      <table>
        <caption>批次列表</caption>
        <thead>
          <tr>
            <th scope="col">批次编号</th>
            <th scope="col">产品</th>
            <th scope="col">追溯码</th>
            <th scope="col">产地</th>
            <th scope="col">生产日期</th>
            <th scope="col">到期日期</th>
            <th scope="col">状态</th>
            <th scope="col">详情</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="batch in batchList.items" :key="batch.id">
            <td>{{ batch.batchNo }}</td>
            <td>{{ productName(batch.productId) }}</td>
            <td>{{ batch.traceCode }}</td>
            <td>{{ batch.origin }}</td>
            <td>{{ batch.productionDate }}</td>
            <td>{{ batch.expiryDate }}</td>
            <td><StatusBadge :label="formatBatchStatus(batch.status)" :tone="batchStatusTone(batch.status)" /></td>
            <td><RouterLink :to="{ name: 'batch-detail', params: { batchId: batch.id } }">查看</RouterLink></td>
          </tr>
          <tr
            v-for="placeholderIndex in placeholderCount"
            :key="`placeholder-${placeholderIndex}`"
            class="pagination-placeholder-row"
            aria-hidden="true"
          >
            <td colspan="8" />
          </tr>
        </tbody>
      </table>
    </PageState>
    <PaginationBar
      :page="batchList.pagination.page"
      :total-pages="batchList.pagination.totalPages"
      :total-items="batchList.pagination.totalItems"
      :page-size="batchList.pagination.pageSize"
      :page-size-options="[10]"
      @change="batchList.goToPage"
      @page-size-change="batchList.setPageSize"
    />
  </section>
</template>

<style scoped>
.batch-list-page {
  display: grid;
  gap: var(--space-5);
}

.batch-list-page > .page-state {
  overflow-x: auto;
}

.batch-list-page > .page-state table {
  min-width: 64rem;
}

.field-with-action {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.field-with-action select {
  min-width: 0;
  flex: 1;
}

.inline-link {
  flex: 0 0 auto;
  white-space: nowrap;
  color: var(--color-accent);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.field-help {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-weight: 400;
  line-height: 1.5;
}

@media (max-width: 48rem) {
  .field-with-action {
    align-items: stretch;
    flex-direction: column;
  }
}

.page-toolbar {
  display: flex;
  justify-content: flex-end;
}

.create-button {
  min-height: 2.5rem;
  padding: var(--space-2) var(--space-4);
}

.create-status {
  margin: 0;
  color: var(--color-success);
  font-size: var(--font-size-sm);
}
</style>
