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
      <MetricCard label="待处理预警" :value="summary.pendingAlertCount" tone="warning" />
      <MetricCard label="临期批次" :value="summary.expiringBatchCount" tone="warning" />
      <MetricCard label="低库存产品" :value="summary.lowStockProductCount" tone="danger" />
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

<style scoped>
.dashboard-summary {
  min-width: 0;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.dashboard-section__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.dashboard-section__header h2,
.dashboard-section__header h3 {
  margin-bottom: var(--space-1);
  font-size: var(--font-size-lg);
}

.dashboard-section__header p {
  margin-bottom: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.dashboard-summary__metrics {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: var(--space-3);
  margin-bottom: var(--space-5);
}

.dashboard-inventory-overview {
  border-top: 1px solid var(--color-border);
  padding-top: var(--space-4);
}

.dashboard-inventory-overview h3 {
  margin-bottom: var(--space-3);
  font-size: var(--font-size-sm);
}

.dashboard-inventory-overview__list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(9rem, 1fr));
  gap: var(--space-2);
  margin: 0;
  padding: 0;
  list-style: none;
}

.dashboard-inventory-overview__list li {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-3);
  border-radius: var(--radius-sm);
  padding: var(--space-2) var(--space-3);
  background: var(--color-surface-muted);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.dashboard-inventory-overview__list strong {
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
}

@media (max-width: 48rem) {
  .dashboard-summary {
    padding: var(--space-4);
  }

  .dashboard-section__header {
    flex-direction: column;
  }

  .dashboard-summary__metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 30rem) {
  .dashboard-summary__metrics {
    grid-template-columns: 1fr;
  }
}

@media (forced-colors: active) {
  .dashboard-summary {
    border: 1px solid CanvasText;
  }
}
</style>
