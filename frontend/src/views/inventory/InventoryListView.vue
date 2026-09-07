<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import {
  createInventoryIssue,
  createInventoryLoss,
  createInventoryReceipt,
  createStocktake,
  createStockTransfer,
  listInventory,
  type InventoryIssueCreatePayload,
  type InventoryLossCreatePayload,
  type InventoryReceiptCreatePayload,
  type StocktakeCreatePayload,
  type StockTransferCreatePayload,
} from '@/api/inventory'
import { listBatchOptions } from '@/api/batches'
import { listWarehouses } from '@/api/warehouses'
import { useListPage, usePageData } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import { getApiErrorMessage } from '@/utils/api-error'

const { items, loading, error, loadData } = useListPage(listInventory)
const warehouseState = usePageData(listWarehouses, [])
const batchState = usePageData(listBatchOptions, [])
const authStore = useAuthStore()
const canWrite = computed(() => authStore.hasPermission('inventory:write'))
const submitting = ref(false)
const formError = ref('')
const successMessage = ref('')

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
    successMessage.value = `入库成功，库存结余为 ${result.quantityAfter}。`
    await loadData()
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
    successMessage.value = `出库成功，库存结余为 ${result.quantityAfter}。`
    await loadData()
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
    successMessage.value = `盘点完成，差异数量为 ${result.differenceQuantity}。`
    await loadData()
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
    successMessage.value = `报损成功，库存结余为 ${result.quantityAfter}。`
    await loadData()
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
    successMessage.value = `调拨成功，调拨单号为 ${result.transferId}。`
    await loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason, '调拨失败，请检查调拨信息')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="inventory-list-page">
    <PageHeader eyebrow="库存运营" title="库存管理" description="查看库存并办理入库业务。" />
    <PageContext />
    <form v-if="canWrite" class="inventory-receipt-form" @submit.prevent="handleReceipt">
      <h2>入库</h2>
      <label>
        仓库
        <select v-model="form.warehouseId" required name="warehouseId">
          <option value="" disabled>请选择仓库</option>
          <option v-for="warehouse in warehouseState.data" :key="warehouse.id" :value="warehouse.id">
            {{ warehouse.name }}（{{ warehouse.code }}）
          </option>
        </select>
      </label>
      <label>
        批次
        <select v-model="form.batchId" required name="batchId">
          <option value="" disabled>请选择批次</option>
          <option v-for="batch in batchState.data" :key="batch.id" :value="batch.id">
            {{ batch.batchNo }}
          </option>
        </select>
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
      <button type="submit" :disabled="submitting || warehouseState.loading || batchState.loading">
        {{ submitting ? '提交中…' : '确认入库' }}
      </button>
      <p v-if="formError" role="alert">{{ formError }}</p>
      <p v-if="warehouseState.error || batchState.error" role="alert">
        {{ warehouseState.error || batchState.error }}
      </p>
      <p v-if="successMessage" role="status">{{ successMessage }}</p>
    </form>
    <form v-if="canWrite" class="inventory-issue-form" @submit.prevent="handleIssue">
      <h2>出库</h2>
      <label>
        仓库
        <select v-model="issueForm.warehouseId" required name="issueWarehouseId">
          <option value="" disabled>请选择仓库</option>
          <option v-for="warehouse in warehouseState.data" :key="warehouse.id" :value="warehouse.id">
            {{ warehouse.name }}（{{ warehouse.code }}）
          </option>
        </select>
      </label>
      <label>
        批次
        <select v-model="issueForm.batchId" required name="issueBatchId">
          <option value="" disabled>请选择批次</option>
          <option v-for="batch in batchState.data" :key="batch.id" :value="batch.id">
            {{ batch.batchNo }}
          </option>
        </select>
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
      <button type="submit" :disabled="submitting || warehouseState.loading || batchState.loading">
        {{ submitting ? '提交中…' : '确认出库' }}
      </button>
      <p v-if="formError" role="alert">{{ formError }}</p>
      <p v-if="successMessage" role="status">{{ successMessage }}</p>
    </form>
    <form v-if="canWrite" class="inventory-stocktake-form" @submit.prevent="handleStocktake">
      <h2>盘点</h2>
      <label>
        仓库
        <select v-model="stocktakeForm.warehouseId" required name="stocktakeWarehouseId">
          <option value="" disabled>请选择仓库</option>
          <option v-for="warehouse in warehouseState.data" :key="warehouse.id" :value="warehouse.id">
            {{ warehouse.name }}（{{ warehouse.code }}）
          </option>
        </select>
      </label>
      <label>
        批次
        <select v-model="stocktakeForm.batchId" required name="stocktakeBatchId">
          <option value="" disabled>请选择批次</option>
          <option v-for="batch in batchState.data" :key="batch.id" :value="batch.id">
            {{ batch.batchNo }}
          </option>
        </select>
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
      <button type="submit" :disabled="submitting || warehouseState.loading || batchState.loading">
        {{ submitting ? '提交中…' : '确认盘点' }}
      </button>
      <p v-if="formError" role="alert">{{ formError }}</p>
      <p v-if="successMessage" role="status">{{ successMessage }}</p>
    </form>
    <form v-if="canWrite" class="inventory-loss-form" @submit.prevent="handleLoss">
      <h2>报损</h2>
      <label>
        仓库
        <select v-model="lossForm.warehouseId" required name="lossWarehouseId">
          <option value="" disabled>请选择仓库</option>
          <option v-for="warehouse in warehouseState.data" :key="warehouse.id" :value="warehouse.id">
            {{ warehouse.name }}（{{ warehouse.code }}）
          </option>
        </select>
      </label>
      <label>
        批次
        <select v-model="lossForm.batchId" required name="lossBatchId">
          <option value="" disabled>请选择批次</option>
          <option v-for="batch in batchState.data" :key="batch.id" :value="batch.id">
            {{ batch.batchNo }}
          </option>
        </select>
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
      <button type="submit" :disabled="submitting || warehouseState.loading || batchState.loading">
        {{ submitting ? '提交中…' : '确认报损' }}
      </button>
      <p v-if="formError" role="alert">{{ formError }}</p>
      <p v-if="successMessage" role="status">{{ successMessage }}</p>
    </form>
    <form v-if="canWrite" class="inventory-transfer-form" @submit.prevent="handleTransfer">
      <h2>仓库调拨</h2>
      <label>
        调出仓库
        <select v-model="transferForm.sourceWarehouseId" required name="sourceWarehouseId">
          <option value="" disabled>请选择调出仓库</option>
          <option v-for="warehouse in warehouseState.data" :key="warehouse.id" :value="warehouse.id">
            {{ warehouse.name }}（{{ warehouse.code }}）
          </option>
        </select>
      </label>
      <label>
        调入仓库
        <select v-model="transferForm.targetWarehouseId" required name="targetWarehouseId">
          <option value="" disabled>请选择调入仓库</option>
          <option v-for="warehouse in warehouseState.data" :key="warehouse.id" :value="warehouse.id">
            {{ warehouse.name }}（{{ warehouse.code }}）
          </option>
        </select>
      </label>
      <label>
        批次
        <select v-model="transferForm.batchId" required name="transferBatchId">
          <option value="" disabled>请选择批次</option>
          <option v-for="batch in batchState.data" :key="batch.id" :value="batch.id">
            {{ batch.batchNo }}
          </option>
        </select>
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
      <button type="submit" :disabled="submitting || warehouseState.loading || batchState.loading">
        {{ submitting ? '提交中…' : '确认调拨' }}
      </button>
      <p v-if="formError" role="alert">{{ formError }}</p>
      <p v-if="successMessage" role="status">{{ successMessage }}</p>
    </form>
    <PageState :loading="loading" :error="error" :empty="items.length === 0" @retry="loadData">
      <table>
        <caption>当前库存</caption>
        <thead>
          <tr><th scope="col">仓库</th><th scope="col">产品</th><th scope="col">批次</th><th scope="col">库存</th><th scope="col">可用库存</th><th scope="col">风险</th></tr>
        </thead>
        <tbody>
          <tr v-for="inventory in items" :key="inventory.id">
            <td>{{ inventory.warehouse.name }}</td>
            <td>{{ inventory.product.name }}</td>
            <td>{{ inventory.batch.batchNo }}</td>
            <td>{{ inventory.quantity }} {{ inventory.product.unit }}</td>
            <td>{{ inventory.availableQuantity }} {{ inventory.product.unit }}</td>
            <td>
              <StatusBadge
                :label="inventory.riskFlags.join('、') || '正常'"
                :tone="inventory.riskFlags.length ? 'warning' : 'success'"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </PageState>
  </section>
</template>

<style scoped>
.inventory-list-page {
  display: grid;
  gap: var(--space-5);
}

.inventory-list-page > form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.inventory-list-page > form h2 {
  grid-column: 1 / -1;
  margin-bottom: 0;
  font-size: var(--font-size-lg);
}

.inventory-list-page > form > label {
  display: grid;
  gap: var(--space-1);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.inventory-list-page > form > label:has(textarea) {
  grid-column: 1 / -1;
}

.inventory-list-page > form > button {
  justify-self: start;
}

.inventory-list-page > form > p {
  grid-column: 1 / -1;
  margin: 0;
  padding: var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
}

.inventory-list-page > form > p[role='alert'] {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.inventory-list-page > form > p[role='status'] {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.inventory-list-page > .page-state {
  overflow-x: auto;
}

.inventory-list-page > .page-state table {
  min-width: 58rem;
}

@media (max-width: 48rem) {
  .inventory-list-page > form {
    grid-template-columns: 1fr;
    padding: var(--space-4);
  }

  .inventory-list-page > form > label:has(textarea),
  .inventory-list-page > form > p {
    grid-column: auto;
  }

  .inventory-list-page > form > button {
    justify-self: stretch;
  }
}
</style>
