<script setup lang="ts">
import MetricCard from './MetricCard.vue'
import type { DashboardSummary as DashboardSummaryData } from '@/types/dashboard'
import { formatDashboardNumber } from '@/utils/dashboard-format'

defineProps<{
  summary: DashboardSummaryData
}>()
</script>

<template>
  <section class="dashboard-summary" aria-labelledby="dashboard-summary-title">
    <header class="dashboard-section__header">
      <div>
        <h2 id="dashboard-summary-title">经营概览</h2>
        <p>统计更新时间：{{ summary.updatedAt }}</p>
      </div>
    </header>

    <div class="dashboard-summary__metrics">
      <MetricCard label="产品数量" :value="summary.productCount" />
      <MetricCard label="批次数量" :value="summary.batchCount" />
      <MetricCard label="待处理预警" :value="summary.pendingAlertCount" />
      <MetricCard label="临期批次" :value="summary.expiringBatchCount" />
      <MetricCard label="低库存产品" :value="summary.lowStockProductCount" />
    </div>

    <section class="dashboard-inventory-overview" aria-labelledby="inventory-overview-title">
      <h3 id="inventory-overview-title">当前库存</h3>
      <ul class="dashboard-inventory-overview__list">
        <li v-for="item in summary.inventoryByUnit" :key="item.unit">
          <span>{{ item.unit }}</span>
          <strong>{{ formatDashboardNumber(item.quantity) }}</strong>
        </li>
      </ul>
    </section>
  </section>
</template>
