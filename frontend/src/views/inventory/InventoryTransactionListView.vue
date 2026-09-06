<script setup lang="ts">
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import { listInventoryTransactions } from '@/api/inventory'
import { useListPage } from '@/composables/usePageData'

const { items, loading, error, loadData } = useListPage(listInventoryTransactions)
</script>

<template>
  <section class="inventory-transaction-list-page">
    <PageHeader title="库存流水" description="不可变库存流水查询占位页面。" />
    <PageContext />
    <PageState :loading="loading" :error="error" :empty="items.length === 0" @retry="loadData">
      <p class="inventory-transaction-list-page__placeholder">已加载 {{ items.length }} 条库存流水。</p>
    </PageState>
  </section>
</template>
