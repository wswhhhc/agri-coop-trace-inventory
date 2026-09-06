<script setup lang="ts">
import PageState from '@/components/common/PageState.vue'
import type { AlertDistribution } from '@/types/dashboard'
import {
  formatAlertSeverity,
  formatAlertType,
  formatDashboardNumber,
} from '@/utils/dashboard-format'

defineProps<{
  distribution: AlertDistribution | null
  loading: boolean
  error: string
}>()

const emit = defineEmits<{
  retry: []
}>()
</script>

<template>
  <section class="dashboard-panel alert-distribution-panel" aria-labelledby="alert-distribution-title">
    <header class="dashboard-section__header">
      <div>
        <h2 id="alert-distribution-title">预警分布</h2>
        <p v-if="distribution">预警总数：{{ formatDashboardNumber(distribution.totalCount) }}</p>
      </div>
    </header>

    <PageState
      :loading="loading"
      :error="error"
      :empty="Boolean(distribution && distribution.items.length === 0) || !distribution"
      empty-message="当前范围暂无预警数据"
      @retry="emit('retry')"
    >
      <table>
        <caption>预警类型及等级分布</caption>
        <thead>
          <tr>
            <th scope="col">预警类型</th>
            <th scope="col">预警等级</th>
            <th scope="col">数量</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in distribution?.items" :key="`${item.alertType}-${item.severity}`">
            <td>{{ formatAlertType(item.alertType) }}</td>
            <td>{{ formatAlertSeverity(item.severity) }}</td>
            <td>{{ formatDashboardNumber(item.count) }}</td>
          </tr>
        </tbody>
      </table>
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
