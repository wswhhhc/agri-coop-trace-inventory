<script setup lang="ts">
import { computed } from 'vue'

import DashboardFilters from '@/components/dashboard/DashboardFilters.vue'
import AlertDistributionPanel from '@/components/dashboard/AlertDistributionPanel.vue'
import DashboardSummary from '@/components/dashboard/DashboardSummary.vue'
import InventoryTrendPanel from '@/components/dashboard/InventoryTrendPanel.vue'
import ProductRankingPanel from '@/components/dashboard/ProductRankingPanel.vue'
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import { useDashboard } from '@/composables/useDashboard'
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
const loading = computed(() => Object.values(moduleLoading).some(Boolean))

function handleSearch(params: DashboardQueryParams): void {
  void loadDashboard(params)
}
</script>

<template>
  <section class="dashboard-page">
    <PageHeader title="数据看板" description="显示当前账号可访问范围内的库存与预警概览。" />
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
    </section>
  </section>
</template>
