<script setup lang="ts">
import { ref } from 'vue'

import { getModelVersion, listModelVersions } from '@/api/forecasting'
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import { useListPage } from '@/composables/usePageData'
import type { ModelVersionSummary } from '@/types/resources'
import { getApiErrorMessage } from '@/utils/api-error'

const { items, loading, error, loadData } = useListPage(listModelVersions)
const selectedModel = ref<ModelVersionSummary | null>(null)
const detailLoading = ref(false)
const detailError = ref('')

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
</script>

<template>
  <section class="forecasting-page">
    <PageHeader title="AI 预测" description="查看模型版本、训练范围和评估指标。" />
    <PageContext />
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
            <td><button type="button" @click="loadDetail(model.id)">查看详情</button></td>
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
