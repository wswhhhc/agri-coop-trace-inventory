<script setup lang="ts">
import PageState from '@/components/common/PageState.vue'
import type { ProductRankingItem } from '@/types/dashboard'
import { formatDashboardNumber } from '@/utils/dashboard-format'

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
