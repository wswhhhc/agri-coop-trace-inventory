<script setup lang="ts">
import PageState from '@/components/common/PageState.vue'
import type { ProductRankingItem } from '@/types/dashboard'
import { formatDashboardNumber } from '@/utils/dashboard-format'
import ProductRankingChart from './ProductRankingChart.vue'

defineProps<{
  items: ProductRankingItem[]
  loading: boolean
  error: string
}>()

const emit = defineEmits<{
  retry: []
}>()
</script>

<template>
  <section class="dashboard-panel product-ranking-panel" aria-labelledby="product-ranking-title">
    <header class="dashboard-section__header">
      <div>
        <h2 id="product-ranking-title">产品出库排行</h2>
        <p>默认展示出库量最高的 10 个产品。</p>
      </div>
    </header>

    <PageState
      :loading="loading"
      :error="error"
      :empty="items.length === 0"
      empty-message="当前范围暂无产品出库数据"
      @retry="emit('retry')"
    >
      <ProductRankingChart :items="items" />
      <table>
        <caption>产品出库排行</caption>
        <thead>
          <tr>
            <th scope="col">排名</th>
            <th scope="col">产品名称</th>
            <th scope="col">单位</th>
            <th scope="col">出库数量</th>
            <th scope="col">出库次数</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in items" :key="item.productId">
            <td>{{ index + 1 }}</td>
            <td>{{ item.productName }}</td>
            <td>{{ item.unit }}</td>
            <td>{{ formatDashboardNumber(item.outboundQuantity) }}</td>
            <td>{{ formatDashboardNumber(item.outboundCount) }}</td>
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
