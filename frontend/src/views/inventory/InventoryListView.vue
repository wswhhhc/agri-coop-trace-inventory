<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import { createInventoryReceipt, listInventory, type InventoryReceiptCreatePayload } from '@/api/inventory'
import { listBatches } from '@/api/batches'
import { listWarehouses } from '@/api/warehouses'
import { useListPage, usePageData } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import { getApiErrorMessage } from '@/utils/api-error'

const { items, loading, error, loadData } = useListPage(listInventory)
const warehouseState = usePageData(listWarehouses, [])
const batchState = usePageData(listBatches, [])
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
</script>

<template>
  <section class="inventory-list-page">
    <PageHeader title="库存管理" description="查看库存并办理入库业务。" />
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
            <td>{{ inventory.riskFlags.join('、') || '正常' }}</td>
          </tr>
        </tbody>
      </table>
    </PageState>
  </section>
</template>
