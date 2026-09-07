<script setup lang="ts">
import { computed } from 'vue'

import PageState from '@/components/common/PageState.vue'
import type { ForecastComparisonItem } from '@/types/dashboard'
import { formatDashboardNumber } from '@/utils/dashboard-format'

const props = defineProps<{
  items: ForecastComparisonItem[]
  loading: boolean
  error: string
  available: boolean
}>()

const emit = defineEmits<{
  retry: []
}>()

const modelVersionCount = computed(
  () => new Set(props.items.map((item) => item.modelVersion)).size,
)

function formatMetric(value: number | undefined): string {
  return value === undefined ? '—' : formatDashboardNumber(value)
}
</script>

<template>
  <section class="dashboard-panel forecast-comparison-panel" aria-labelledby="forecast-comparison-title">
    <header class="dashboard-section__header">
      <div>
        <h2 id="forecast-comparison-title">预测与测试集对比</h2>
        <p>对比预测需求与预测区间内的实际出库量，辅助判断模型效果。</p>
      </div>
    </header>

    <div v-if="!available" class="forecast-comparison-panel__unavailable" role="status">
      当前账号没有预测查看权限，暂不展示测试集对比数据。
    </div>

    <PageState
      v-else
      :loading="loading"
      :error="error"
      :empty="items.length === 0"
      :preserve-content-on-loading="items.length > 0"
      empty-message="当前范围暂无预测测试集对比数据"
      @retry="emit('retry')"
    >
      <div class="forecast-comparison-panel__summary" aria-label="预测对比摘要">
        <div>
          <span>对比记录</span>
          <strong>{{ items.length }}</strong>
        </div>
        <div>
          <span>模型版本</span>
          <strong>{{ modelVersionCount }}</strong>
        </div>
        <p>数量按产品单位分别解读，不跨单位汇总。</p>
      </div>

      <div class="forecast-comparison-panel__table-wrap">
        <table>
          <caption>预测需求、测试集实际出库量、误差及模型版本</caption>
          <thead>
            <tr>
              <th scope="col">预测区间</th>
              <th scope="col">产品 ID</th>
              <th scope="col">预测需求</th>
              <th scope="col">测试集实际出库量</th>
              <th scope="col">绝对误差</th>
              <th scope="col">模型版本</th>
              <th scope="col">MAE</th>
              <th scope="col">RMSE</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.forecastResultId">
              <td>{{ item.forecastStartDate }} ～ {{ item.forecastEndDate }}</td>
              <td class="forecast-comparison-panel__id">{{ item.productId }}</td>
              <td>{{ formatDashboardNumber(item.predictedDemand) }}</td>
              <td>{{ formatDashboardNumber(item.actualDemand) }}</td>
              <td class="forecast-comparison-panel__error">
                {{ formatDashboardNumber(item.absoluteError) }}
              </td>
              <td><code>{{ item.modelVersion }}</code></td>
              <td>{{ formatMetric(item.metrics.mae) }}</td>
              <td>{{ formatMetric(item.metrics.rmse) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </PageState>
  </section>
</template>

<style scoped>
.dashboard-panel {
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

.dashboard-section__header h2 {
  margin-bottom: var(--space-1);
  font-size: var(--font-size-lg);
}

.dashboard-section__header p {
  margin-bottom: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.forecast-comparison-panel__summary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.forecast-comparison-panel__summary > div {
  display: grid;
  min-width: 9rem;
  gap: var(--space-1);
  border-radius: var(--radius-md);
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface-muted);
}

.forecast-comparison-panel__summary span,
.forecast-comparison-panel__summary p {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.forecast-comparison-panel__summary strong {
  color: var(--color-text);
  font-size: var(--font-size-xl);
  font-variant-numeric: tabular-nums;
}

.forecast-comparison-panel__summary p {
  margin: 0;
}

.forecast-comparison-panel__table-wrap {
  overflow-x: auto;
}

.forecast-comparison-panel table {
  width: 100%;
  min-width: 72rem;
  font-size: var(--font-size-md);
}

.forecast-comparison-panel caption {
  padding-top: var(--space-4);
  padding-bottom: var(--space-4);
  font-size: var(--font-size-md);
}

.forecast-comparison-panel th {
  padding-top: var(--space-4);
  padding-bottom: var(--space-4);
  font-size: var(--font-size-sm);
}

.forecast-comparison-panel td {
  padding-top: var(--space-4);
  padding-bottom: var(--space-4);
}

.forecast-comparison-panel__id {
  max-width: 12rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: var(--font-size-xs);
}

.forecast-comparison-panel code {
  border-radius: var(--radius-sm);
  padding: var(--space-1) var(--space-2);
  background: var(--color-brand-soft);
  color: var(--color-brand);
  font-size: var(--font-size-xs);
}

.forecast-comparison-panel__error {
  color: var(--color-warning);
  font-weight: 600;
}

.forecast-comparison-panel__unavailable {
  border: 1px dashed var(--color-border-strong);
  border-radius: var(--radius-md);
  padding: var(--space-5);
  background: var(--color-surface-muted);
  color: var(--color-text-secondary);
  text-align: center;
}

@media (max-width: 48rem) {
  .dashboard-panel {
    padding: var(--space-4);
  }

  .dashboard-section__header {
    flex-direction: column;
  }
}

@media (forced-colors: active) {
  .dashboard-panel {
    border: 1px solid CanvasText;
  }
}
</style>
