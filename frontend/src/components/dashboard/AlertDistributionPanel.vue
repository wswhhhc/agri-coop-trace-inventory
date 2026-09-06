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
