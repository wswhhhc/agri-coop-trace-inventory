<script setup lang="ts">
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import { listWarehouses } from '@/api/warehouses'
import { useListPage } from '@/composables/usePageData'

const { items, loading, error, loadData } = useListPage(listWarehouses)
</script>

<template>
  <section class="warehouse-list-page">
    <PageHeader title="仓库管理" description="仓库及授权范围占位页面。" />
    <PageContext />
    <PageState :loading="loading" :error="error" :empty="items.length === 0" @retry="loadData">
      <p class="warehouse-list-page__placeholder">已加载 {{ items.length }} 条仓库数据。</p>
    </PageState>
  </section>
</template>
