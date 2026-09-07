<script setup lang="ts">
import { computed } from 'vue'

import { listInventoryTrendsPage } from '@/api/dashboard'
import DashboardFilters from '@/components/dashboard/DashboardFilters.vue'
import AlertDistributionPanel from '@/components/dashboard/AlertDistributionPanel.vue'
import DashboardSummary from '@/components/dashboard/DashboardSummary.vue'
import ForecastComparisonPanel from '@/components/dashboard/ForecastComparisonPanel.vue'
import InventoryTrendPanel from '@/components/dashboard/InventoryTrendPanel.vue'
import ProductRankingPanel from '@/components/dashboard/ProductRankingPanel.vue'
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import { useDashboard } from '@/composables/useDashboard'
import { usePaginatedList } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import type { DashboardQueryParams } from '@/types/dashboard'

const authStore = useAuthStore()
const canReadForecastComparison = authStore.hasPermission('model:read')
const {
  query,
  summary,
  alertDistribution,
  productRanking,
  forecastComparison,
  loading: moduleLoading,
  errors: moduleErrors,
  loadDashboard,
  retry,
} = useDashboard({ canReadForecastComparison })
const inventoryTrendList = usePaginatedList((pagination) =>
  listInventoryTrendsPage({ ...pagination, ...query.value }),
  100,
)
const loading = computed(
  () => Object.values(moduleLoading).some(Boolean) || inventoryTrendList.loading,
)

function handleSearch(params: DashboardQueryParams): void {
  void loadDashboard(params).then(() => inventoryTrendList.loadData(1))
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

      <ForecastComparisonPanel
        :items="forecastComparison"
        :loading="moduleLoading.forecastComparison"
        :error="moduleErrors.forecastComparison"
        :available="canReadForecastComparison"
        @retry="retry('forecastComparison')"
      />
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
.forecast-comparison-panel {
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

</style>
