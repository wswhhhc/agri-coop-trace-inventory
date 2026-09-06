<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import {
  activateModel,
  getForecastingTask,
  getModelVersion,
  listModelVersions,
  submitModelTrainingTask,
} from '@/api/forecasting'
import { listProducts } from '@/api/products'
import { listWarehouses } from '@/api/warehouses'
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import { useListPage } from '@/composables/usePageData'
import { usePageData } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import type { ModelVersionSummary, TaskSummary } from '@/types/resources'
import { getApiErrorMessage } from '@/utils/api-error'

const { items, loading, error, loadData } = useListPage(listModelVersions)
const authStore = useAuthStore()
const canActivate = computed(
  () => authStore.role === 'COOPERATIVE_ADMIN' && authStore.hasPermission('model:manage'),
)
const canTrain = computed(
  () => authStore.role === 'COOPERATIVE_ADMIN' && authStore.hasPermission('model:manage'),
)
const warehouseState = usePageData(listWarehouses, [])
const productState = usePageData(listProducts, [])
const selectedModel = ref<ModelVersionSummary | null>(null)
const detailLoading = ref(false)
const detailError = ref('')
const activatingId = ref<string | null>(null)
const actionError = ref('')
const successMessage = ref('')
const trainingSubmitting = ref(false)
const trainingError = ref('')
const trainingTask = ref<TaskSummary | null>(null)
const trainingForm = reactive({
  warehouseId: '',
  productId: '',
  startDate: '',
  endDate: '',
  testRatio: 0.2,
  randomSeed: 42,
})

async function loadDetail(modelVersionId: string): Promise<void> {
  detailLoading.value = true
  detailError.value = ''
  try {
    selectedModel.value = await getModelVersion(modelVersionId)
  } catch (reason) {
    detailError.value = getApiErrorMessage(reason, '模型详情加载失败')
  } finally {
    detailLoading.value = false
  }
}

async function handleActivate(modelVersionId: string): Promise<void> {
  activatingId.value = modelVersionId
  actionError.value = ''
  successMessage.value = ''
  try {
    await activateModel(modelVersionId)
    successMessage.value = '模型激活成功。'
    await loadData()
    if (selectedModel.value?.id === modelVersionId) {
      selectedModel.value = await getModelVersion(modelVersionId)
    }
  } catch (reason) {
    actionError.value = getApiErrorMessage(reason, '模型激活失败')
  } finally {
    activatingId.value = null
  }
}

function wait(milliseconds: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds))
}

async function handleTrainingSubmit(): Promise<void> {
  trainingSubmitting.value = true
  trainingError.value = ''
  trainingTask.value = null
  try {
    trainingTask.value = await submitModelTrainingTask({
      modelType: 'XGBOOST',
      scope: { warehouseId: trainingForm.warehouseId, productId: trainingForm.productId },
      trainingRange: { startDate: trainingForm.startDate, endDate: trainingForm.endDate },
      testRatio: trainingForm.testRatio,
      randomSeed: trainingForm.randomSeed,
      parameters: {},
    })
    for (let attempt = 0; attempt < 20; attempt += 1) {
      if (trainingTask.value.status === 'SUCCESS' || trainingTask.value.status === 'FAILURE') break
      await wait(1000)
      trainingTask.value = await getForecastingTask(trainingTask.value.id)
    }
    await loadData()
  } catch (reason) {
    trainingError.value = getApiErrorMessage(reason, '模型训练任务失败')
  } finally {
    trainingSubmitting.value = false
  }
}
</script>

<template>
  <section class="forecasting-page">
    <PageHeader title="AI 预测" description="查看模型版本、训练范围和评估指标。" />
    <PageContext />
    <form v-if="canTrain" class="model-training-form" @submit.prevent="handleTrainingSubmit">
      <h2>提交模型训练</h2>
      <label>
        仓库
        <select v-model="trainingForm.warehouseId" required>
          <option value="" disabled>请选择仓库</option>
          <option v-for="warehouse in warehouseState.data" :key="warehouse.id" :value="warehouse.id">
            {{ warehouse.name }}
          </option>
        </select>
      </label>
      <label>
        产品
        <select v-model="trainingForm.productId" required>
          <option value="" disabled>请选择产品</option>
          <option v-for="product in productState.data" :key="product.id" :value="product.id">
            {{ product.name }}
          </option>
        </select>
      </label>
      <label>开始日期 <input v-model="trainingForm.startDate" type="date" required /></label>
      <label>结束日期 <input v-model="trainingForm.endDate" type="date" required /></label>
      <label>测试比例 <input v-model.number="trainingForm.testRatio" type="number" min="0.01" max="0.99" step="0.01" required /></label>
      <label>随机种子 <input v-model.number="trainingForm.randomSeed" type="number" min="0" step="1" required /></label>
      <button type="submit" :disabled="trainingSubmitting">{{ trainingSubmitting ? '训练中…' : '提交训练任务' }}</button>
      <p v-if="trainingTask" role="status">训练任务：{{ trainingTask.status }}，进度 {{ trainingTask.progress }}%</p>
      <p v-if="trainingTask?.errorMessage" role="alert">{{ trainingTask.errorMessage }}</p>
      <p v-if="trainingError" role="alert">{{ trainingError }}</p>
    </form>
    <p v-if="actionError" role="alert">{{ actionError }}</p>
    <p v-if="successMessage" role="status">{{ successMessage }}</p>
    <PageState :loading="loading" :error="error" :empty="items.length === 0" @retry="loadData">
      <table>
        <caption>模型版本列表</caption>
        <thead>
          <tr>
            <th scope="col">版本</th>
            <th scope="col">模型类型</th>
            <th scope="col">训练区间</th>
            <th scope="col">数据类型</th>
            <th scope="col">状态</th>
            <th scope="col">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="model in items" :key="model.id">
            <td>{{ model.version }}</td>
            <td>{{ model.modelType }}</td>
            <td>{{ model.trainingStartDate }} ～ {{ model.trainingEndDate }}</td>
            <td>{{ model.dataType }}</td>
            <td>{{ model.isActive ? '已激活' : '未激活' }}</td>
            <td>
              <button type="button" @click="loadDetail(model.id)">查看详情</button>
              <button
                v-if="canActivate && !model.isActive"
                type="button"
                :disabled="activatingId === model.id"
                @click="handleActivate(model.id)"
              >
                {{ activatingId === model.id ? '激活中…' : '激活' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </PageState>
    <aside v-if="detailLoading || detailError || selectedModel" class="model-version-detail">
      <h2>模型版本详情</h2>
      <p v-if="detailLoading">详情加载中…</p>
      <p v-else-if="detailError" role="alert">{{ detailError }}</p>
      <dl v-else-if="selectedModel">
        <div><dt>版本</dt><dd>{{ selectedModel.version }}</dd></div>
        <div><dt>模型类型</dt><dd>{{ selectedModel.modelType }}</dd></div>
        <div><dt>仓库</dt><dd>{{ selectedModel.warehouseId }}</dd></div>
        <div><dt>产品</dt><dd>{{ selectedModel.productId }}</dd></div>
        <div><dt>随机种子</dt><dd>{{ selectedModel.randomSeed }}</dd></div>
        <div><dt>参数</dt><dd><pre>{{ JSON.stringify(selectedModel.parameters, null, 2) }}</pre></dd></div>
        <div><dt>指标</dt><dd><pre>{{ JSON.stringify(selectedModel.metrics, null, 2) }}</pre></dd></div>
      </dl>
    </aside>
  </section>
</template>
