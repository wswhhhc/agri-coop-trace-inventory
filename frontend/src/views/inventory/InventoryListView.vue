<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import FilterBar from '@/components/common/FilterBar.vue'
import PageState from '@/components/common/PageState.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import {
  createInventoryIssue,
  createInventoryLoss,
  createInventoryReceipt,
  createStocktake,
  createStockTransfer,
  listInventoryPage,
  type InventoryIssueCreatePayload,
  type InventoryListParams,
  type InventoryLossCreatePayload,
  type InventoryReceiptCreatePayload,
  type StocktakeCreatePayload,
  type StockTransferCreatePayload,
} from '@/api/inventory'
import { listBatchOptions } from '@/api/batches'
import { listProductOptions } from '@/api/products'
import { listWarehouses } from '@/api/warehouses'
import CreateFormModal from '@/components/common/CreateFormModal.vue'
import SelectField, { type SelectFieldOption } from '@/components/common/SelectField.vue'
import { usePageData, usePaginatedList } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import { getApiErrorMessage } from '@/utils/api-error'
import { formatInventoryRiskFlags } from '@/utils/inventory-format'

const filters = reactive<
  Pick<InventoryListParams, 'warehouseId' | 'productId' | 'batchId' | 'stockRisk' | 'keyword'>
>({
  warehouseId: '',
  productId: '',
  batchId: '',
  stockRisk: '',
  keyword: '',
})
const inventoryList = usePaginatedList((pagination) => listInventoryPage({ ...pagination, ...filters }))
const warehouseState = usePageData(listWarehouses, [])
const batchState = usePageData(listBatchOptions, [])
const productState = usePageData(() => listProductOptions({ isActive: true, pageSize: 100 }), [])
const warehouseOptions = computed<SelectFieldOption[]>(() =>
  warehouseState.data.map((warehouse) => ({
    value: warehouse.id,
    label: `${warehouse.name}（${warehouse.code}）`,
  })),
)
const batchOptions = computed<SelectFieldOption[]>(() =>
  batchState.data.map((batch) => ({ value: batch.id, label: batch.batchNo })),
)
const productOptions = computed<SelectFieldOption[]>(() =>
  productState.data.map((product) => ({
    value: product.id,
    label: `${product.name}（${product.code}）`,
  })),
)
const filterWarehouseOptions = computed<SelectFieldOption[]>(() => [
  { value: '', label: '全部仓库' },
  ...warehouseOptions.value,
])
const filterProductOptions = computed<SelectFieldOption[]>(() => [
  { value: '', label: '全部产品' },
  ...productOptions.value,
])
const filterBatchOptions = computed<SelectFieldOption[]>(() => [
  { value: '', label: '全部批次' },
  ...batchOptions.value,
])
const authStore = useAuthStore()
const canWrite = computed(() => authStore.hasPermission('inventory:write'))
type InventoryOperation = 'receipt' | 'issue' | 'stocktake' | 'loss' | 'transfer'

const activeOperation = ref<InventoryOperation | null>(null)
const submitting = ref(false)
const formError = ref('')
const successMessage = ref('')
const operationOptionsError = computed(() => warehouseState.error || batchState.error)
const riskOptions = [
  { value: '', label: '全部风险' },
  { value: 'LOW_STOCK', label: '库存不足' },
  { value: 'NEAR_EXPIRY', label: '临近过期' },
  { value: 'OVERSTOCK', label: '库存积压' },
]

function applyFilters(): void {
  void inventoryList.loadData(1)
}

function resetFilters(): void {
  filters.warehouseId = ''
  filters.productId = ''
  filters.batchId = ''
  filters.stockRisk = ''
  filters.keyword = ''
  void inventoryList.loadData(1)
}

function getLocalDateTimeValue(): string {
  const now = new Date()
  return new Date(now.getTime() - now.getTimezoneOffset() * 60_000).toISOString().slice(0, 16)
}

const form = reactive<InventoryReceiptCreatePayload & { occurredAtInput: string }>({
  warehouseId: '',
  batchId: '',
  quantity: 0,
  occurredAt: '',
  occurredAtInput: getLocalDateTimeValue(),
  referenceNo: null,
  remark: null,
})
const issueForm = reactive<InventoryIssueCreatePayload & { occurredAtInput: string }>({
  warehouseId: '',
  batchId: '',
  quantity: 0,
  occurredAt: '',
  occurredAtInput: getLocalDateTimeValue(),
  referenceNo: null,
  destination: null,
  remark: null,
})
const stocktakeForm = reactive<StocktakeCreatePayload & { occurredAtInput: string }>({
  warehouseId: '',
  batchId: '',
  countedQuantity: 0,
  occurredAt: '',
  occurredAtInput: getLocalDateTimeValue(),
  reason: '',
  remark: null,
})
const lossForm = reactive<InventoryLossCreatePayload & { occurredAtInput: string }>({
  warehouseId: '',
  batchId: '',
  quantity: 0,
  occurredAt: '',
  occurredAtInput: getLocalDateTimeValue(),
  reason: '',
  remark: null,
})
const transferForm = reactive<StockTransferCreatePayload & { occurredAtInput: string }>({
  sourceWarehouseId: '',
  targetWarehouseId: '',
  batchId: '',
  quantity: 0,
  occurredAt: '',
  occurredAtInput: getLocalDateTimeValue(),
  remark: null,
})

function openOperation(operation: InventoryOperation): void {
  if (submitting.value) return
  resetOperationForm(operation)
  formError.value = ''
  successMessage.value = ''
  activeOperation.value = operation
}

function closeOperation(): void {
  if (submitting.value) return
  activeOperation.value = null
  formError.value = ''
}

function resetOperationForm(operation: InventoryOperation): void {
  if (operation === 'receipt') resetForm()
  if (operation === 'issue') resetIssueForm()
  if (operation === 'stocktake') resetStocktakeForm()
  if (operation === 'loss') resetLossForm()
  if (operation === 'transfer') resetTransferForm()
}

function resetForm(): void {
  form.warehouseId = ''
  form.batchId = ''
  form.quantity = 0
  form.occurredAt = ''
  form.occurredAtInput = getLocalDateTimeValue()
  form.referenceNo = null
  form.remark = null
}

async function handleReceipt(): Promise<void> {
  submitting.value = true
  formError.value = ''
  successMessage.value = ''
  try {
    form.occurredAt = new Date(form.occurredAtInput).toISOString()
    const result = await createInventoryReceipt(
      {
        warehouseId: form.warehouseId,
        batchId: form.batchId,
        quantity: form.quantity,
        occurredAt: form.occurredAt,
        referenceNo: form.referenceNo?.trim() || null,
        remark: form.remark?.trim() || null,
      },
      crypto.randomUUID(),
    )
    resetForm()
    activeOperation.value = null
    successMessage.value = `入库成功，库存结余为 ${result.quantityAfter}。`
    await inventoryList.loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    submitting.value = false
  }
}

function resetIssueForm(): void {
  issueForm.warehouseId = ''
  issueForm.batchId = ''
  issueForm.quantity = 0
  issueForm.occurredAt = ''
  issueForm.occurredAtInput = getLocalDateTimeValue()
  issueForm.referenceNo = null
  issueForm.destination = null
  issueForm.remark = null
}

async function handleIssue(): Promise<void> {
  submitting.value = true
  formError.value = ''
  successMessage.value = ''
  try {
    issueForm.occurredAt = new Date(issueForm.occurredAtInput).toISOString()
    const result = await createInventoryIssue(
      {
        warehouseId: issueForm.warehouseId,
        batchId: issueForm.batchId,
        quantity: issueForm.quantity,
        occurredAt: issueForm.occurredAt,
        referenceNo: issueForm.referenceNo?.trim() || null,
        destination: issueForm.destination?.trim() || null,
        remark: issueForm.remark?.trim() || null,
      },
      crypto.randomUUID(),
    )
    resetIssueForm()
    activeOperation.value = null
    successMessage.value = `出库成功，库存结余为 ${result.quantityAfter}。`
    await inventoryList.loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    submitting.value = false
  }
}

function resetStocktakeForm(): void {
  stocktakeForm.warehouseId = ''
  stocktakeForm.batchId = ''
  stocktakeForm.countedQuantity = 0
  stocktakeForm.occurredAt = ''
  stocktakeForm.occurredAtInput = getLocalDateTimeValue()
  stocktakeForm.reason = ''
  stocktakeForm.remark = null
}

async function handleStocktake(): Promise<void> {
  submitting.value = true
  formError.value = ''
  successMessage.value = ''
  try {
    stocktakeForm.occurredAt = new Date(stocktakeForm.occurredAtInput).toISOString()
    const result = await createStocktake(
      {
        warehouseId: stocktakeForm.warehouseId,
        batchId: stocktakeForm.batchId,
        countedQuantity: stocktakeForm.countedQuantity,
        occurredAt: stocktakeForm.occurredAt,
        reason: stocktakeForm.reason.trim(),
        remark: stocktakeForm.remark?.trim() || null,
      },
      crypto.randomUUID(),
    )
    resetStocktakeForm()
    activeOperation.value = null
    successMessage.value = `盘点完成，差异数量为 ${result.differenceQuantity}。`
    await inventoryList.loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    submitting.value = false
  }
}

function resetLossForm(): void {
  lossForm.warehouseId = ''
  lossForm.batchId = ''
  lossForm.quantity = 0
  lossForm.occurredAt = ''
  lossForm.occurredAtInput = getLocalDateTimeValue()
  lossForm.reason = ''
  lossForm.remark = null
}

async function handleLoss(): Promise<void> {
  submitting.value = true
  formError.value = ''
  successMessage.value = ''
  try {
    lossForm.occurredAt = new Date(lossForm.occurredAtInput).toISOString()
    const result = await createInventoryLoss(
      {
        warehouseId: lossForm.warehouseId,
        batchId: lossForm.batchId,
        quantity: lossForm.quantity,
        occurredAt: lossForm.occurredAt,
        reason: lossForm.reason.trim(),
        remark: lossForm.remark?.trim() || null,
      },
      crypto.randomUUID(),
    )
    resetLossForm()
    activeOperation.value = null
    successMessage.value = `报损成功，库存结余为 ${result.quantityAfter}。`
    await inventoryList.loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    submitting.value = false
  }
}

function resetTransferForm(): void {
  transferForm.sourceWarehouseId = ''
  transferForm.targetWarehouseId = ''
  transferForm.batchId = ''
  transferForm.quantity = 0
  transferForm.occurredAt = ''
  transferForm.occurredAtInput = getLocalDateTimeValue()
  transferForm.remark = null
}

async function handleTransfer(): Promise<void> {
  submitting.value = true
  formError.value = ''
  successMessage.value = ''
  try {
    if (transferForm.sourceWarehouseId === transferForm.targetWarehouseId) {
      throw new Error('调出仓库和调入仓库不能相同')
    }
    transferForm.occurredAt = new Date(transferForm.occurredAtInput).toISOString()
    const result = await createStockTransfer(
      {
        sourceWarehouseId: transferForm.sourceWarehouseId,
        targetWarehouseId: transferForm.targetWarehouseId,
        batchId: transferForm.batchId,
        quantity: transferForm.quantity,
        occurredAt: transferForm.occurredAt,
        remark: transferForm.remark?.trim() || null,
      },
      crypto.randomUUID(),
    )
    resetTransferForm()
    activeOperation.value = null
    successMessage.value = `调拨成功，调拨单号为 ${result.transferId}。`
    await inventoryList.loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason, '调拨失败，请检查调拨信息')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="inventory-list-page">
    <div v-if="canWrite" class="inventory-operation-toolbar" role="toolbar" aria-label="库存操作">
      <button type="button" @click="openOperation('receipt')">入库</button>
      <button type="button" @click="openOperation('issue')">出库</button>
      <button type="button" @click="openOperation('stocktake')">盘点</button>
      <button type="button" @click="openOperation('loss')">报损</button>
      <button type="button" @click="openOperation('transfer')">仓库调拨</button>
    </div>
    <p v-if="successMessage" class="inventory-operation-status" role="status">{{ successMessage }}</p>

    <CreateFormModal
      :open="activeOperation === 'receipt'"
      title="入库"
      submit-label="确认入库"
      :submitting="submitting"
      :submit-disabled="warehouseState.loading || batchState.loading"
      :error="formError || operationOptionsError"
      @close="closeOperation"
      @submit="handleReceipt"
    >
      <label>
        仓库
        <SelectField v-model="form.warehouseId" :options="warehouseOptions" name="warehouseId" required placeholder="请选择仓库" />
      </label>
      <label>
        批次
        <SelectField v-model="form.batchId" :options="batchOptions" name="batchId" required placeholder="请选择批次" />
      </label>
      <label>
        数量
        <input v-model.number="form.quantity" type="number" min="0.001" step="0.001" required name="quantity" />
      </label>
      <label>
        入库时间
        <input v-model="form.occurredAtInput" type="datetime-local" required name="occurredAt" />
      </label>
      <label>
        参考单号
        <input v-model="form.referenceNo" maxlength="100" name="referenceNo" />
      </label>
      <label>
        备注
        <textarea v-model="form.remark" maxlength="500" name="remark" />
      </label>
    </CreateFormModal>

    <CreateFormModal
      :open="activeOperation === 'issue'"
      title="出库"
      submit-label="确认出库"
      :submitting="submitting"
      :submit-disabled="warehouseState.loading || batchState.loading"
      :error="formError || operationOptionsError"
      @close="closeOperation"
      @submit="handleIssue"
    >
      <label>
        仓库
        <SelectField v-model="issueForm.warehouseId" :options="warehouseOptions" name="issueWarehouseId" required placeholder="请选择仓库" />
      </label>
      <label>
        批次
        <SelectField v-model="issueForm.batchId" :options="batchOptions" name="issueBatchId" required placeholder="请选择批次" />
      </label>
      <label>
        数量
        <input v-model.number="issueForm.quantity" type="number" min="0.001" step="0.001" required name="issueQuantity" />
      </label>
      <label>
        出库时间
        <input v-model="issueForm.occurredAtInput" type="datetime-local" required name="issueOccurredAt" />
      </label>
      <label>
        目的地
        <input v-model="issueForm.destination" maxlength="255" name="destination" />
      </label>
      <label>
        参考单号
        <input v-model="issueForm.referenceNo" maxlength="100" name="issueReferenceNo" />
      </label>
      <label>
        备注
        <textarea v-model="issueForm.remark" maxlength="500" name="issueRemark" />
      </label>
    </CreateFormModal>

    <CreateFormModal
      :open="activeOperation === 'stocktake'"
      title="盘点"
      submit-label="确认盘点"
      :submitting="submitting"
      :submit-disabled="warehouseState.loading || batchState.loading"
      :error="formError || operationOptionsError"
      @close="closeOperation"
      @submit="handleStocktake"
    >
      <label>
        仓库
        <SelectField v-model="stocktakeForm.warehouseId" :options="warehouseOptions" name="stocktakeWarehouseId" required placeholder="请选择仓库" />
      </label>
      <label>
        批次
        <SelectField v-model="stocktakeForm.batchId" :options="batchOptions" name="stocktakeBatchId" required placeholder="请选择批次" />
      </label>
      <label>
        实盘数量
        <input v-model.number="stocktakeForm.countedQuantity" type="number" min="0" step="0.001" required name="countedQuantity" />
      </label>
      <label>
        盘点时间
        <input v-model="stocktakeForm.occurredAtInput" type="datetime-local" required name="stocktakeOccurredAt" />
      </label>
      <label>
        原因
        <input v-model="stocktakeForm.reason" maxlength="500" required name="reason" />
      </label>
      <label>
        备注
        <textarea v-model="stocktakeForm.remark" maxlength="500" name="stocktakeRemark" />
      </label>
    </CreateFormModal>

    <CreateFormModal
      :open="activeOperation === 'loss'"
      title="报损"
      submit-label="确认报损"
      :submitting="submitting"
      :submit-disabled="warehouseState.loading || batchState.loading"
      :error="formError || operationOptionsError"
      @close="closeOperation"
      @submit="handleLoss"
    >
      <label>
        仓库
        <SelectField v-model="lossForm.warehouseId" :options="warehouseOptions" name="lossWarehouseId" required placeholder="请选择仓库" />
      </label>
      <label>
        批次
        <SelectField v-model="lossForm.batchId" :options="batchOptions" name="lossBatchId" required placeholder="请选择批次" />
      </label>
      <label>
        报损数量
        <input v-model.number="lossForm.quantity" type="number" min="0.001" step="0.001" required name="lossQuantity" />
      </label>
      <label>
        报损时间
        <input v-model="lossForm.occurredAtInput" type="datetime-local" required name="lossOccurredAt" />
      </label>
      <label>
        原因
        <input v-model="lossForm.reason" maxlength="500" required name="lossReason" />
      </label>
      <label>
        备注
        <textarea v-model="lossForm.remark" maxlength="500" name="lossRemark" />
      </label>
    </CreateFormModal>

    <CreateFormModal
      :open="activeOperation === 'transfer'"
      title="仓库调拨"
      submit-label="确认调拨"
      :submitting="submitting"
      :submit-disabled="warehouseState.loading || batchState.loading"
      :error="formError || operationOptionsError"
      @close="closeOperation"
      @submit="handleTransfer"
    >
      <label>
        调出仓库
        <SelectField v-model="transferForm.sourceWarehouseId" :options="warehouseOptions" name="sourceWarehouseId" required placeholder="请选择调出仓库" />
      </label>
      <label>
        调入仓库
        <SelectField v-model="transferForm.targetWarehouseId" :options="warehouseOptions" name="targetWarehouseId" required placeholder="请选择调入仓库" />
      </label>
      <label>
        批次
        <SelectField v-model="transferForm.batchId" :options="batchOptions" name="transferBatchId" required placeholder="请选择批次" />
      </label>
      <label>
        数量
        <input v-model.number="transferForm.quantity" type="number" min="0.001" step="0.001" required name="transferQuantity" />
      </label>
      <label>
        调拨时间
        <input v-model="transferForm.occurredAtInput" type="datetime-local" required name="transferOccurredAt" />
      </label>
      <label>
        备注
        <textarea v-model="transferForm.remark" maxlength="500" name="transferRemark" />
      </label>
    </CreateFormModal>
    <FilterBar @submit="applyFilters" @reset="resetFilters">
      <label>
        仓库
        <SelectField v-model="filters.warehouseId" :options="filterWarehouseOptions" name="inventoryWarehouseFilter" />
      </label>
      <label>
        产品
        <SelectField v-model="filters.productId" :options="filterProductOptions" name="inventoryProductFilter" />
      </label>
      <label>
        批次
        <SelectField v-model="filters.batchId" :options="filterBatchOptions" name="inventoryBatchFilter" />
      </label>
      <label>
        库存风险
        <SelectField v-model="filters.stockRisk" :options="riskOptions" name="inventoryRiskFilter" />
      </label>
      <label>
        关键字
        <input
          v-model="filters.keyword"
          name="inventoryKeywordFilter"
          placeholder="产品名称或批次编号"
          maxlength="100"
        />
      </label>
    </FilterBar>
    <p v-if="warehouseState.error || productState.error || batchState.error" class="inventory-filter-error" role="alert">
      {{ warehouseState.error || productState.error || batchState.error }}
    </p>
    <PageState
      :loading="inventoryList.loading"
      :error="inventoryList.error"
      :empty="inventoryList.items.length === 0"
      @retry="inventoryList.loadData"
    >
      <table>
        <caption>当前库存</caption>
        <thead>
          <tr><th scope="col">仓库</th><th scope="col">产品</th><th scope="col">批次</th><th scope="col">库存</th><th scope="col">可用库存</th><th scope="col">风险</th></tr>
        </thead>
        <tbody>
          <tr v-for="inventory in inventoryList.items" :key="inventory.id">
            <td>{{ inventory.warehouse.name }}</td>
            <td>{{ inventory.product.name }}</td>
            <td>{{ inventory.batch.batchNo }}</td>
            <td>{{ inventory.quantity }} {{ inventory.product.unit }}</td>
            <td>{{ inventory.availableQuantity }} {{ inventory.product.unit }}</td>
            <td>
              <StatusBadge
                :label="formatInventoryRiskFlags(inventory.riskFlags)"
                :tone="inventory.riskFlags.length ? 'warning' : 'success'"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </PageState>
    <PaginationBar
      :page="inventoryList.pagination.page"
      :total-pages="inventoryList.pagination.totalPages"
      :total-items="inventoryList.pagination.totalItems"
      :page-size="inventoryList.pagination.pageSize"
      @change="inventoryList.goToPage"
      @page-size-change="inventoryList.setPageSize"
    />
  </section>
</template>

<style scoped>
.inventory-list-page {
  display: grid;
  gap: var(--space-5);
}

.inventory-operation-toolbar {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: var(--space-3);
}

.inventory-operation-toolbar button {
  min-width: 7rem;
}

.inventory-operation-status {
  margin: 0;
  padding: var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  background: var(--color-success-soft);
  color: var(--color-success);
}

.inventory-list-page > .page-state {
  overflow-x: auto;
}

.inventory-list-page > .page-state table {
  min-width: 58rem;
}

.inventory-filter-error {
  margin: calc(var(--space-5) * -1) 0 0;
  color: var(--color-danger);
  font-size: var(--font-size-sm);
}

@media (max-width: 48rem) {
  .inventory-operation-toolbar {
    justify-content: stretch;
  }

  .inventory-operation-toolbar button {
    flex: 1 1 8rem;
  }
}
</style>
