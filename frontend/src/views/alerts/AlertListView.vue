<script setup lang="ts">
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import { listAlerts } from '@/api/alerts'
import { useListPage } from '@/composables/usePageData'

const { items, loading, error, loadData } = useListPage(listAlerts)
</script>

<template>
  <section class="alert-list-page">
    <PageHeader title="预警中心" description="库存和批次预警查询占位页面。" />
    <PageContext />
    <PageState :loading="loading" :error="error" :empty="items.length === 0" @retry="loadData">
      <p class="alert-list-page__placeholder">已加载 {{ items.length }} 条预警数据。</p>
    </PageState>
  </section>
</template>
