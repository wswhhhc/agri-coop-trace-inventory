<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import { createBatch, listBatches, type BatchCreatePayload } from '@/api/batches'
import { listProducts } from '@/api/products'
import { useListPage, usePageData } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import { getApiErrorMessage } from '@/utils/api-error'

const { items, loading, error, loadData } = useListPage(listBatches)
const productState = usePageData(listProducts, [])
const authStore = useAuthStore()
const canManage = computed(() => authStore.hasPermission('batch:manage'))
const submitting = ref(false)
const formError = ref('')
const successMessage = ref('')
const form = reactive<BatchCreatePayload>({
  productId: '',
  batchNo: '',
  origin: '',
  productionDate: '',
  expiryDate: '',
  responsiblePerson: null,
})

function productName(productId: string): string {
  return productState.data.value.find((product) => product.id === productId)?.name ?? '—'
}

function resetForm(): void {
  form.productId = ''
  form.batchNo = ''
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
      batchNo: form.batchNo.trim(),
      origin: form.origin.trim(),
      productionDate: form.productionDate,
      expiryDate: form.expiryDate,
      responsiblePerson: form.responsiblePerson?.trim() || null,
    })
    resetForm()
    successMessage.value = `批次创建成功，追溯码为 ${created.traceCode}。`
    await loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="batch-list-page">
    <PageHeader title="批次管理" description="创建和查看农产品生产批次。" />
    <PageContext />
    <form v-if="canManage" class="batch-create-form" @submit.prevent="handleSubmit">
      <h2>新增批次</h2>
      <label>
        产品
        <select v-model="form.productId" name="productId" required>
          <option value="" disabled>请选择产品</option>
          <option v-for="product in productState.data" :key="product.id" :value="product.id">
            {{ product.name }}（{{ product.code }}）
          </option>
        </select>
      </label>
      <label>
        批次编号
        <input v-model="form.batchNo" name="batchNo" required maxlength="64" />
      </label>
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
    <PageState :loading="loading" :error="error" :empty="items.length === 0" @retry="loadData">
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
          </tr>
        </thead>
        <tbody>
          <tr v-for="batch in items" :key="batch.id">
            <td>{{ batch.batchNo }}</td>
            <td>{{ productName(batch.productId) }}</td>
            <td>{{ batch.traceCode }}</td>
            <td>{{ batch.origin }}</td>
            <td>{{ batch.productionDate }}</td>
            <td>{{ batch.expiryDate }}</td>
            <td>{{ batch.status }}</td>
          </tr>
        </tbody>
      </table>
    </PageState>
  </section>
</template>
