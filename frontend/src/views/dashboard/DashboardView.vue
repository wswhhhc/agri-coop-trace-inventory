<script setup lang="ts">
import { computed } from 'vue'

import { listForecastResultsPage } from '@/api/forecasting'
import { listInventoryTrendsPage } from '@/api/dashboard'
import DashboardFilters from '@/components/dashboard/DashboardFilters.vue'
import AlertDistributionPanel from '@/components/dashboard/AlertDistributionPanel.vue'
import DashboardSummary from '@/components/dashboard/DashboardSummary.vue'
import InventoryTrendPanel from '@/components/dashboard/InventoryTrendPanel.vue'
import ProductRankingPanel from '@/components/dashboard/ProductRankingPanel.vue'
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import PageState from '@/components/common/PageState.vue'
import { useDashboard } from '@/composables/useDashboard'
import { usePaginatedList } from '@/composables/usePageData'
import type { DashboardQueryParams } from '@/types/dashboard'

const {
  query,
  summary,
  alertDistribution,
  productRanking,
  loading: moduleLoading,
  errors: moduleErrors,
  loadDashboard,
  retry,
} = useDashboard()
const inventoryTrendList = usePaginatedList((pagination) =>
  listInventoryTrendsPage({ ...pagination, ...query.value }),
)
const forecastState = usePaginatedList(listForecastResultsPage)
const loading = computed(
  () =>
    Object.values(moduleLoading).some(Boolean) ||
    inventoryTrendList.loading ||
    forecastState.loading,
)

function handleSearch(params: DashboardQueryParams): void {
  void loadDashboard(params).then(() =>
    Promise.all([inventoryTrendList.loadData(1), forecastState.loadData(1)]),
  )
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
        :items="inventoryTrendList.items"
        :loading="inventoryTrendList.loading"
        :error="inventoryTrendList.error"
        :pagination="inventoryTrendList.pagination"
        @retry="inventoryTrendList.loadData"
        @change="inventoryTrendList.goToPage"
        @page-size-change="inventoryTrendList.setPageSize"
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
          :empty="forecastState.items.length === 0"
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
              <tr v-for="item in forecastState.items" :key="item.id">
                <td>{{ item.forecastStartDate }} ～ {{ item.forecastEndDate }}</td>
                <td>{{ item.predictedDemand }}</td>
                <td>{{ item.currentStock }}</td>
                <td>{{ item.recommendedReplenishment }}</td>
              </tr>
            </tbody>
          </table>
        </PageState>
        <PaginationBar
          :page="forecastState.pagination.page"
          :total-pages="forecastState.pagination.totalPages"
          :total-items="forecastState.pagination.totalItems"
          :page-size="forecastState.pagination.pageSize"
          :page-size-options="[10]"
          @change="forecastState.goToPage"
          @page-size-change="forecastState.setPageSize"
        />
      </section>
    </section>
  </section>
</template>

<style scoped>
.dashboard-page__modules {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: var(--space-5);
}

.dashboard-module {
  min-width: 0;
}

.dashboard-module--summary,
.dashboard-module--forecast {
  grid-column: 1 / -1;
}

.dashboard-page__modules > .inventory-trend-panel {
  grid-column: span 8;
}

.dashboard-page__modules > .alert-distribution-panel {
  grid-column: span 4;
}

.dashboard-page__modules > .product-ranking-panel {
  grid-column: 1 / -1;
}

.dashboard-module--forecast {
  overflow-x: auto;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.dashboard-module--forecast table {
  min-width: 38rem;
}

.dashboard-module--forecast h2 {
  margin-bottom: var(--space-4);
  font-size: var(--font-size-lg);
}

@media (max-width: 48rem) {
  .dashboard-page__modules {
    grid-template-columns: 1fr;
  }

  .dashboard-page__modules > .inventory-trend-panel,
  .dashboard-page__modules > .alert-distribution-panel,
  .dashboard-page__modules > .product-ranking-panel {
    grid-column: 1;
  }
}

@media (forced-colors: active) {
  .dashboard-module--forecast {
    border: 1px solid CanvasText;
  }
}
</style>
