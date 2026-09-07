<script setup lang="ts">
import { computed } from 'vue'

import type { ProductRankingItem } from '@/types/dashboard'
import { formatDashboardNumber } from '@/utils/dashboard-format'

const props = defineProps<{
  items: ProductRankingItem[]
}>()

const rows = computed(() => props.items.slice(0, 5))
const maximum = computed(() => Math.max(1, ...rows.value.map((item) => item.outboundQuantity)))

function barWidth(quantity: number): string {
  return Math.max(8, (quantity / maximum.value) * 100).toFixed(1) + '%'
}
</script>

<template>
  <section v-if="rows.length" class="product-ranking-chart" aria-labelledby="product-ranking-chart-title">
    <header class="product-ranking-chart__header">
      <h3 id="product-ranking-chart-title">出库量 Top 5</h3>
      <span>按出库量降序</span>
    </header>
    <ol class="product-ranking-chart__list">
      <li v-for="(item, index) in rows" :key="item.productId">
        <span class="product-ranking-chart__rank">{{ index + 1 }}</span>
        <div class="product-ranking-chart__body">
          <div class="product-ranking-chart__label">
            <span>{{ item.productName }}（{{ item.unit }}）</span>
            <strong>{{ formatDashboardNumber(item.outboundQuantity) }}</strong>
          </div>
          <div
            class="product-ranking-chart__track"
            role="img"
            :aria-label="item.productName + '出库量' + item.outboundQuantity + item.unit"
          >
            <span class="product-ranking-chart__bar" :style="{ width: barWidth(item.outboundQuantity) }"></span>
          </div>
        </div>
      </li>
    </ol>
  </section>
</template>

<style scoped>
.product-ranking-chart {
  display: grid;
  gap: var(--space-3);
  margin-bottom: var(--space-5);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  background: var(--color-surface-muted);
}

.product-ranking-chart__header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-3);
}

.product-ranking-chart__header h3 {
  margin: 0;
  font-size: var(--font-size-md);
}

.product-ranking-chart__header span {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.product-ranking-chart__list {
  display: grid;
  gap: var(--space-3);
  margin: 0;
  padding: 0;
  list-style: none;
}

.product-ranking-chart__list li {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.product-ranking-chart__rank {
  display: grid;
  flex: 0 0 1.75rem;
  width: 1.75rem;
  height: 1.75rem;
  place-items: center;
  border-radius: var(--radius-pill);
  background: var(--color-brand-soft);
  color: var(--color-brand);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.product-ranking-chart__body {
  min-width: 0;
  flex: 1;
}

.product-ranking-chart__label {
  display: flex;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-1);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.product-ranking-chart__label span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-ranking-chart__label strong {
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
}

.product-ranking-chart__track {
  height: 0.5rem;
  overflow: hidden;
  border-radius: var(--radius-pill);
  background: var(--color-border);
}

.product-ranking-chart__bar {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--color-brand);
}

@media (forced-colors: active) {
  .product-ranking-chart {
    border: 1px solid CanvasText;
  }
}
</style>
