<script setup lang="ts">
import { computed } from 'vue'

import { listForecastResults } from '@/api/forecasting'
import DashboardFilters from '@/components/dashboard/DashboardFilters.vue'
import AlertDistributionPanel from '@/components/dashboard/AlertDistributionPanel.vue'
import DashboardSummary from '@/components/dashboard/DashboardSummary.vue'
import InventoryTrendPanel from '@/components/dashboard/InventoryTrendPanel.vue'
import ProductRankingPanel from '@/components/dashboard/ProductRankingPanel.vue'
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import { useDashboard } from '@/composables/useDashboard'
import { usePageData } from '@/composables/usePageData'
import type { DashboardQueryParams } from '@/types/dashboard'

const {
  summary,
  inventoryTrends,
  alertDistribution,
  productRanking,
  loading: moduleLoading,
  errors: moduleErrors,
  loadDashboard,
  retry,
} = useDashboard()
const forecastState = usePageData(listForecastResults, [])
const loading = computed(() => Object.values(moduleLoading).some(Boolean))

function handleSearch(params: DashboardQueryParams): void {
  void loadDashboard(params)
}
</script>

<template>
  <section class="dashboard-page">
    <PageHeader eyebrow="运营总览" title="数据看板" description="显示当前账号可访问范围内的库存与预警概览。" />
    <PageContext />

    <DashboardFilters :loading="loading" @search="handleSearch" />

    <section class="dashboard-page__modules">
      <section class="dashboard-module dashboard-module--summary">
        <PageState
          :loading="moduleLoading.summary"
          :error="moduleErrors.summary"
          :empty="!summary"
          empty-message="暂无汇总数据"
          @retry="retry('summary')"
        >
          <DashboardSummary v-if="summary" :summary="summary" />
        </PageState>
      </section>

      <InventoryTrendPanel
        :items="inventoryTrends"
        :loading="moduleLoading.inventoryTrends"
        :error="moduleErrors.inventoryTrends"
        @retry="retry('inventoryTrends')"
      />

      <AlertDistributionPanel
        :distribution="alertDistribution"
        :loading="moduleLoading.alertDistribution"
        :error="moduleErrors.alertDistribution"
        @retry="retry('alertDistribution')"
      />

      <ProductRankingPanel
        :items="productRanking"
        :loading="moduleLoading.productRanking"
        :error="moduleErrors.productRanking"
        @retry="retry('productRanking')"
      />

      <section class="dashboard-module dashboard-module--forecast">
        <h2>需求预测对比</h2>
        <PageState
          :loading="forecastState.loading"
          :error="forecastState.error"
          :empty="forecastState.data.length === 0"
          empty-message="暂无预测结果"
          @retry="forecastState.loadData"
        >
          <table>
            <caption>预测需求、当前库存与建议补货</caption>
            <thead>
              <tr>
                <th scope="col">预测区间</th>
                <th scope="col">预测需求</th>
                <th scope="col">当前库存</th>
                <th scope="col">建议补货</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in forecastState.data" :key="item.id">
                <td>{{ item.forecastStartDate }} ～ {{ item.forecastEndDate }}</td>
                <td>{{ item.predictedDemand }}</td>
                <td>{{ item.currentStock }}</td>
                <td>{{ item.recommendedReplenishment }}</td>
              </tr>
            </tbody>
          </table>
        </PageState>
      </section>
    </section>
  </section>
</template>
