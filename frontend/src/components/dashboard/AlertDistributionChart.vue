<script setup lang="ts">
import { computed } from 'vue'

import type { AlertDistribution } from '@/types/dashboard'
import { formatAlertSeverity, formatAlertType, formatDashboardNumber } from '@/utils/dashboard-format'

const props = defineProps<{
  distribution: AlertDistribution | null
}>()

const rows = computed(() =>
  [...(props.distribution?.items ?? [])].sort((a, b) => b.count - a.count),
)
const maximum = computed(() => Math.max(1, ...rows.value.map((item) => item.count)))

function barWidth(count: number): string {
  return Math.max(8, (count / maximum.value) * 100).toFixed(1) + '%'
}
</script>

<template>
  <section v-if="rows.length" class="alert-distribution-chart" aria-labelledby="alert-distribution-chart-title">
    <header class="alert-distribution-chart__header">
      <h3 id="alert-distribution-chart-title">预警类型与等级</h3>
      <span>按数量降序</span>
    </header>
    <ol class="alert-distribution-chart__list">
      <li v-for="item in rows" :key="item.alertType + '-' + item.severity">
        <div class="alert-distribution-chart__label">
          <span>{{ formatAlertType(item.alertType) }} · {{ formatAlertSeverity(item.severity) }}</span>
          <strong>{{ formatDashboardNumber(item.count) }}</strong>
        </div>
        <div
          class="alert-distribution-chart__track"
          role="img"
          :aria-label="formatAlertType(item.alertType) + formatAlertSeverity(item.severity) + '预警' + item.count + '条'"
        >
          <span class="alert-distribution-chart__bar" :style="{ width: barWidth(item.count) }"></span>
        </div>
      </li>
    </ol>
  </section>
</template>

<style scoped>
.alert-distribution-chart {
  display: grid;
  gap: var(--space-3);
  margin-bottom: var(--space-5);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  background: var(--color-surface-muted);
}

.alert-distribution-chart__header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-3);
}

.alert-distribution-chart__header h3 {
  margin: 0;
  font-size: var(--font-size-md);
}

.alert-distribution-chart__header span {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.alert-distribution-chart__list {
  display: grid;
  gap: var(--space-3);
  margin: 0;
  padding: 0;
  list-style: none;
}

.alert-distribution-chart__label {
  display: flex;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-1);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.alert-distribution-chart__label strong {
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
}

.alert-distribution-chart__track {
  height: 0.5rem;
  overflow: hidden;
  border-radius: var(--radius-pill);
  background: var(--color-border);
}

.alert-distribution-chart__bar {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--color-warning);
}

@media (forced-colors: active) {
  .alert-distribution-chart {
    border: 1px solid CanvasText;
  }
}
</style>
