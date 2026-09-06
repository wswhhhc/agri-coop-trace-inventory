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

const dashboard = useDashboard()
const loading = computed(() => Object.values(dashboard.loading).some(Boolean))

function handleSearch(params: DashboardQueryParams): void {
  void dashboard.loadDashboard(params)
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
          :loading="dashboard.loading.summary"
          :error="dashboard.errors.summary"
          :empty="!dashboard.summary"
          empty-message="暂无汇总数据"
          @retry="dashboard.retry('summary')"
        >
          <DashboardSummary v-if="dashboard.summary" :summary="dashboard.summary" />
        </PageState>
      </section>

      <InventoryTrendPanel
        :items="dashboard.inventoryTrends"
        :loading="dashboard.loading.inventoryTrends"
        :error="dashboard.errors.inventoryTrends"
        @retry="dashboard.retry('inventoryTrends')"
      />

      <AlertDistributionPanel
        :distribution="dashboard.alertDistribution"
        :loading="dashboard.loading.alertDistribution"
        :error="dashboard.errors.alertDistribution"
        @retry="dashboard.retry('alertDistribution')"
      />

      <ProductRankingPanel
        :items="dashboard.productRanking"
        :loading="dashboard.loading.productRanking"
        :error="dashboard.errors.productRanking"
        @retry="dashboard.retry('productRanking')"
      />
    </section>
  </section>
</template>
