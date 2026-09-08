<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import PaginationBar from '@/components/common/PaginationBar.vue'
import PageState from '@/components/common/PageState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import GeneratedCodeField from '@/components/common/GeneratedCodeField.vue'
import { createBatch, listBatches, type BatchCreatePayload } from '@/api/batches'
import { listProductOptions } from '@/api/products'
import { getPagePlaceholderCount, usePageData, usePaginatedList } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import { getApiErrorMessage } from '@/utils/api-error'

const batchList = usePaginatedList(listBatches)
const placeholderCount = computed(() =>
  getPagePlaceholderCount(batchList.pagination.pageSize, batchList.items.length),
)
const productState = usePageData(
  () => listProductOptions({ isActive: true, pageSize: 100 }),
  [],
)
const authStore = useAuthStore()
const canManage = computed(() => authStore.hasPermission('batch:manage'))
const canManageProducts = computed(() => authStore.hasPermission('product:manage'))
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
    <form v-if="canManage" class="batch-create-form" @submit.prevent="handleSubmit">
      <h2>新增批次</h2>
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
      <button type="submit" :disabled="submitting || productState.loading">
        {{ submitting ? '提交中…' : '创建' }}
      </button>
      <p v-if="formError" role="alert">{{ formError }}</p>
      <p v-if="productState.error" role="alert">{{ productState.error }}</p>
      <p v-if="successMessage" role="status">{{ successMessage }}</p>
    </form>
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
            <td><StatusBadge :label="batch.status" :tone="batchStatusTone(batch.status)" /></td>
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

.batch-create-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.batch-create-form h2 {
  grid-column: 1 / -1;
  margin-bottom: 0;
  font-size: var(--font-size-lg);
}

.batch-create-form > label {
  display: grid;
  gap: var(--space-1);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 600;
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

.batch-create-form > button {
  justify-self: start;
}

.batch-create-form > p {
  grid-column: 1 / -1;
  margin: 0;
  padding: var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
}

.batch-create-form > p[role='alert'] {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.batch-create-form > p[role='status'] {
  background: var(--color-success-soft);
  color: var(--color-success);
}

@media (max-width: 48rem) {
  .batch-create-form {
    grid-template-columns: 1fr;
    padding: var(--space-4);
  }

  .batch-create-form h2,
  .batch-create-form > p {
    grid-column: auto;
  }

  .batch-create-form > button {
    justify-self: stretch;
  }

  .field-with-action {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
