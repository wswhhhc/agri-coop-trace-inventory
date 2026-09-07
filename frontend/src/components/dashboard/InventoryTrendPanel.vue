<script setup lang="ts">
import { computed } from 'vue'

import PageState from '@/components/common/PageState.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import type { InventoryTrend } from '@/types/dashboard'
import type { PaginationMeta } from '@/types/api'
import { formatDashboardNumber } from '@/utils/dashboard-format'

const props = defineProps<{
  items: InventoryTrend[]
  loading: boolean
  error: string
  pagination: PaginationMeta
}>()

const emit = defineEmits<{
  retry: []
  change: [page: number]
  'page-size-change': [pageSize: number]
}>()

const groupedTrends = computed(() => {
  const groups = new Map<string, InventoryTrend[]>()
  for (const item of props.items) {
    const group = groups.get(item.unit) ?? []
    group.push(item)
    groups.set(item.unit, group)
  }
  return Array.from(groups, ([unit, items]) => ({ unit, items }))
})
</script>

<template>
  <section class="dashboard-panel inventory-trend-panel" aria-labelledby="inventory-trend-title">
    <header class="dashboard-section__header">
      <div>
        <h2 id="inventory-trend-title">库存趋势</h2>
        <p>按日期和计量单位展示入库、出库及期末库存。</p>
      </div>
    </header>

    <PageState
      :loading="loading"
      :error="error"
      :empty="items.length === 0"
      empty-message="当前范围暂无库存趋势数据"
      @retry="emit('retry')"
    >
      <div class="inventory-trend-tables">
        <section v-for="group in groupedTrends" :key="group.unit" class="inventory-trend-group">
          <h3>{{ group.unit }}</h3>
          <table>
            <caption>{{ group.unit }}库存趋势</caption>
            <thead>
              <tr>
                <th scope="col">日期</th>
                <th scope="col">单位</th>
                <th scope="col">入库数量</th>
                <th scope="col">出库数量</th>
                <th scope="col">期末库存</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in group.items" :key="`${item.date}-${item.unit}`">
                <td>{{ item.date }}</td>
                <td>{{ item.unit }}</td>
                <td>{{ formatDashboardNumber(item.inboundQuantity) }}</td>
                <td>{{ formatDashboardNumber(item.outboundQuantity) }}</td>
                <td>{{ formatDashboardNumber(item.endingQuantity) }}</td>
              </tr>
            </tbody>
          </table>
        </section>
      </div>
      <div class="inventory-trend-table-note" aria-label="库存趋势数据说明">
        当前以明细表展示趋势数据，已包含入库、出库和期末库存。
      </div>
      <PaginationBar
        :page="pagination.page"
        :total-pages="pagination.totalPages"
        :total-items="pagination.totalItems"
        :page-size="pagination.pageSize"
        :page-size-options="[10]"
        @change="emit('change', $event)"
        @page-size-change="emit('page-size-change', $event)"
      />
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

.inventory-trend-tables {
  display: grid;
  gap: var(--space-5);
}

.inventory-trend-group {
  overflow-x: auto;
}

.inventory-trend-group h3 {
  margin-bottom: var(--space-2);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.inventory-trend-group table {
  min-width: 38rem;
}

.inventory-trend-table-note {
  margin-top: var(--space-4);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
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
