<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import {
  activateModel,
  getForecastResult,
  getForecastingTask,
  getModelVersion,
  listForecastResults,
  listModelVersions,
  submitForecastTask,
  submitModelTrainingTask,
} from '@/api/forecasting'
import { listProducts } from '@/api/products'
import { listWarehouses } from '@/api/warehouses'
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TaskProgress from '@/components/common/TaskProgress.vue'
import { useListPage } from '@/composables/usePageData'
import { usePageData } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import type {
  ForecastResultDetailSummary,
  ModelVersionSummary,
  TaskSummary,
} from '@/types/resources'
import { getApiErrorMessage } from '@/utils/api-error'

const { items, loading, error, loadData } = useListPage(listModelVersions)
const forecastResults = useListPage(listForecastResults)
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
const selectedForecast = ref<ForecastResultDetailSummary | null>(null)
const forecastDetailLoading = ref(false)
const forecastDetailError = ref('')
const detailLoading = ref(false)
const detailError = ref('')
const activatingId = ref<string | null>(null)
const actionError = ref('')
const successMessage = ref('')
const trainingSubmitting = ref(false)
const trainingError = ref('')
const trainingTask = ref<TaskSummary | null>(null)
const forecastSubmitting = ref(false)
const forecastError = ref('')
const forecastTask = ref<TaskSummary | null>(null)
const forecastForm = reactive({
  warehouseId: '',
  productId: '',
  horizon: 'SEVEN_DAYS' as 'SEVEN_DAYS' | 'THIRTY_DAYS',
})
const trainingForm = reactive({
  warehouseId: '',
  productId: '',
  startDate: '',
  endDate: '',
  testRatio: 0.2,
  randomSeed: 42,
})

function modelStatusTone(active: boolean): 'success' | 'neutral' {
  return active ? 'success' : 'neutral'
}

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

async function loadForecastDetail(forecastResultId: string): Promise<void> {
  forecastDetailLoading.value = true
  forecastDetailError.value = ''
  try {
    selectedForecast.value = await getForecastResult(forecastResultId)
  } catch (reason) {
    forecastDetailError.value = getApiErrorMessage(reason, '预测结果加载失败')
  } finally {
    forecastDetailLoading.value = false
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

async function handleForecastSubmit(): Promise<void> {
  forecastSubmitting.value = true
  forecastError.value = ''
  forecastTask.value = null
  try {
    forecastTask.value = await submitForecastTask(forecastForm)
    for (let attempt = 0; attempt < 20; attempt += 1) {
      if (forecastTask.value.status === 'SUCCESS' || forecastTask.value.status === 'FAILURE') break
      await wait(1000)
      forecastTask.value = await getForecastingTask(forecastTask.value.id)
    }
  } catch (reason) {
    forecastError.value = getApiErrorMessage(reason, '需求预测任务失败')
  } finally {
    forecastSubmitting.value = false
  }
}
</script>

<template>
  <section class="forecasting-page">
    <PageHeader eyebrow="智能决策" title="AI 预测" description="查看模型版本、训练范围和评估指标。" />
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
      <TaskProgress v-if="trainingTask" label="模型训练任务" :status="trainingTask.status" :progress="trainingTask.progress" />
      <p v-if="trainingTask?.errorMessage" role="alert">{{ trainingTask.errorMessage }}</p>
      <p v-if="trainingError" role="alert">{{ trainingError }}</p>
    </form>
    <form v-if="canTrain" class="forecast-task-form" @submit.prevent="handleForecastSubmit">
      <h2>提交需求预测</h2>
      <label>
        仓库
        <select v-model="forecastForm.warehouseId" required>
          <option value="" disabled>请选择仓库</option>
          <option v-for="warehouse in warehouseState.data" :key="warehouse.id" :value="warehouse.id">
            {{ warehouse.name }}
          </option>
        </select>
      </label>
      <label>
        产品
        <select v-model="forecastForm.productId" required>
          <option value="" disabled>请选择产品</option>
          <option v-for="product in productState.data" :key="product.id" :value="product.id">
            {{ product.name }}
          </option>
        </select>
      </label>
      <label>
        预测周期
        <select v-model="forecastForm.horizon" required>
          <option value="SEVEN_DAYS">未来 7 天</option>
          <option value="THIRTY_DAYS">未来 30 天</option>
        </select>
      </label>
      <button type="submit" :disabled="forecastSubmitting">
        {{ forecastSubmitting ? '预测中…' : '提交预测任务' }}
      </button>
      <TaskProgress v-if="forecastTask" label="需求预测任务" :status="forecastTask.status" :progress="forecastTask.progress" />
      <p v-if="forecastTask?.errorMessage" role="alert">{{ forecastTask.errorMessage }}</p>
      <p v-if="forecastError" role="alert">{{ forecastError }}</p>
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
            <td><StatusBadge :label="model.isActive ? '已激活' : '未激活'" :tone="modelStatusTone(model.isActive)" /></td>
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
    <section class="forecast-results">
      <PageState
        :loading="forecastResults.loading"
        :error="forecastResults.error"
        :empty="forecastResults.items.length === 0"
        empty-message="暂无预测结果"
        @retry="forecastResults.loadData"
      >
        <table>
          <caption>需求预测结果</caption>
          <thead>
            <tr>
              <th scope="col">预测区间</th>
              <th scope="col">预测需求</th>
              <th scope="col">当前库存</th>
              <th scope="col">建议补货</th>
              <th scope="col">生成时间</th>
              <th scope="col">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="result in forecastResults.items" :key="result.id">
              <td>{{ result.forecastStartDate }} ～ {{ result.forecastEndDate }}</td>
              <td>{{ result.predictedDemand }}</td>
              <td>{{ result.currentStock }}</td>
              <td>{{ result.recommendedReplenishment }}</td>
              <td>{{ result.generatedAt }}</td>
              <td><button type="button" @click="loadForecastDetail(result.id)">查看详情</button></td>
            </tr>
          </tbody>
        </table>
      </PageState>
      <aside v-if="forecastDetailLoading || forecastDetailError || selectedForecast" class="forecast-result-detail">
        <h2>预测结果详情</h2>
        <p v-if="forecastDetailLoading">详情加载中…</p>
        <p v-else-if="forecastDetailError" role="alert">{{ forecastDetailError }}</p>
        <div v-else-if="selectedForecast">
          <p>数据类型：{{ selectedForecast.dataType }}</p>
          <p>重要因素：{{ selectedForecast.importantFactors.join('、') || '暂无' }}</p>
          <p>限制说明：{{ selectedForecast.limitationNotice }}</p>
          <table>
            <caption>逐日预测点</caption>
            <thead><tr><th scope="col">日期</th><th scope="col">预测量</th><th scope="col">区间</th></tr></thead>
            <tbody>
              <tr v-for="point in selectedForecast.points" :key="point.id">
                <td>{{ point.forecastDate }}</td>
                <td>{{ point.predictedQuantity }}</td>
                <td>{{ point.lowerBound }} ～ {{ point.upperBound }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </aside>
    </section>
  </section>
</template>
