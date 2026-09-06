<script setup lang="ts">
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import { listForecastResults } from '@/api/forecasting'
import { useListPage } from '@/composables/usePageData'

const { items, loading, error, loadData } = useListPage(listForecastResults)
</script>

<template>
  <section class="forecasting-page">
    <PageHeader title="AI 预测" description="模型版本和需求预测结果占位页面。" />
    <PageContext />
    <PageState :loading="loading" :error="error" :empty="items.length === 0" @retry="loadData">
      <p class="forecasting-page__placeholder">已加载 {{ items.length }} 条预测结果。</p>
    </PageState>
  </section>
</template>
