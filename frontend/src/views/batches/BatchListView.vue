<script setup lang="ts">
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import { listBatches } from '@/api/batches'
import { useListPage } from '@/composables/usePageData'

const { items, loading, error, loadData } = useListPage(listBatches)
</script>

<template>
  <section class="batch-list-page">
    <PageHeader title="批次管理" description="农产品批次和追溯信息占位页面。" />
    <PageContext />
    <PageState :loading="loading" :error="error" :empty="items.length === 0" @retry="loadData">
      <p class="batch-list-page__placeholder">已加载 {{ items.length }} 条批次数据。</p>
    </PageState>
  </section>
</template>
