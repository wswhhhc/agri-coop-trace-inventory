<script setup lang="ts">
import { computed } from 'vue'

import { listInventoryTrendsPage } from '@/api/dashboard'
import DashboardFilters from '@/components/dashboard/DashboardFilters.vue'
import AlertDistributionPanel from '@/components/dashboard/AlertDistributionPanel.vue'
import DashboardSummary from '@/components/dashboard/DashboardSummary.vue'
import ForecastComparisonPanel from '@/components/dashboard/ForecastComparisonPanel.vue'
import InventoryTrendPanel from '@/components/dashboard/InventoryTrendPanel.vue'
import ProductRankingPanel from '@/components/dashboard/ProductRankingPanel.vue'
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
  10,
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
    <section class="dashboard-intro" aria-labelledby="dashboard-intro-title">
      <div class="dashboard-intro__copy">
        <p class="dashboard-intro__eyebrow">今日运营概览</p>
        <h1 id="dashboard-intro-title">把每一批农产品，<br /><em>管得更清楚。</em></h1>
        <p>从库存流动到临期预警，快速掌握合作社今天最需要关注的业务。</p>
      </div>
      <div class="dashboard-intro__route" aria-label="批次流转路径">
        <span class="dashboard-intro__route-label">批次流转</span>
        <div class="dashboard-intro__route-line">
          <i></i><b></b><i></i><b></b><i></i>
        </div>
        <span>采收 → 质检 → 入库 → 交付</span>
      </div>
    </section>
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
  gap: var(--space-6);
}

.dashboard-page {
  display: grid;
  gap: var(--space-6);
}

.dashboard-intro {
  position: relative;
  display: flex;
  min-height: 15rem;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-8);
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--color-brand) 25%, var(--color-border));
  border-radius: 1.25rem;
  padding: clamp(1.5rem, 4vw, 2.75rem);
  background:
    radial-gradient(circle at 84% 20%, rgb(201 154 61 / 25%), transparent 10rem),
    linear-gradient(118deg, var(--color-brand-950), var(--color-brand-900) 62%, var(--color-brand-800));
  box-shadow: var(--shadow-md);
}

.dashboard-intro::after {
  position: absolute;
  right: 12%;
  top: -45%;
  width: 16rem;
  height: 24rem;
  border: 1px solid rgb(255 255 255 / 12%);
  border-radius: 50%;
  transform: rotate(34deg);
  content: '';
}

.dashboard-intro__copy {
  position: relative;
  z-index: 1;
}

.dashboard-intro__eyebrow {
  margin-bottom: var(--space-3);
  color: var(--color-grain-500);
  font-size: var(--font-size-sm);
  font-weight: 700;
}

.dashboard-intro h1 {
  margin-bottom: var(--space-4);
  color: var(--color-white);
  font-family: var(--font-family-display);
  font-size: clamp(2rem, 4vw, 3.6rem);
  font-weight: 600;
  letter-spacing: -0.07em;
  line-height: 1.1;
}

.dashboard-intro h1 em {
  color: var(--color-grain-100);
  font-style: normal;
}

.dashboard-intro__copy > p:last-child {
  max-width: 31rem;
  margin-bottom: 0;
  color: rgb(217 237 225 / 78%);
  font-size: var(--font-size-sm);
}

.dashboard-intro__route {
  position: relative;
  z-index: 1;
  display: grid;
  min-width: 14rem;
  gap: var(--space-3);
  color: rgb(217 237 225 / 78%);
  font-size: var(--font-size-xs);
  text-align: right;
}

.dashboard-intro__route-label {
  color: var(--color-grain-500);
  font-weight: 700;
}

.dashboard-intro__route-line {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.35rem;
}

.dashboard-intro__route-line i,
.dashboard-intro__route-line b {
  display: block;
}

.dashboard-intro__route-line i {
  width: 0.55rem;
  height: 0.55rem;
  border: 2px solid var(--color-grain-500);
  border-radius: var(--radius-pill);
}

.dashboard-intro__route-line b {
  width: 2.5rem;
  height: 1px;
  background: rgb(248 237 207 / 52%);
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
  .dashboard-intro {
    min-height: 13rem;
    align-items: flex-start;
  }

  .dashboard-intro__route {
    display: none;
  }

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
