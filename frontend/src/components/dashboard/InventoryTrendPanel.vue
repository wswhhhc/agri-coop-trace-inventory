<script setup lang="ts">
import { computed } from 'vue'

import PageState from '@/components/common/PageState.vue'
import type { InventoryTrend } from '@/types/dashboard'
import { formatDashboardNumber } from '@/utils/dashboard-format'

const props = defineProps<{
  items: InventoryTrend[]
  loading: boolean
  error: string
}>()

const emit = defineEmits<{
  retry: []
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
      <div class="inventory-trend-chart-placeholder" aria-label="库存趋势图表预留区域">
        后续在这里接入库存趋势图表
      </div>
    </PageState>
  </section>
</template>
