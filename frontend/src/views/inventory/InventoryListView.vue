<script setup lang="ts">
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import { listInventory } from '@/api/inventory'
import { useListPage } from '@/composables/usePageData'

const { items, loading, error, loadData } = useListPage(listInventory)
</script>

<template>
  <section class="inventory-list-page">
    <PageHeader title="库存管理" description="当前库存查询占位页面。" />
    <PageContext />
    <PageState :loading="loading" :error="error" :empty="items.length === 0" @retry="loadData">
      <p class="inventory-list-page__placeholder">已加载 {{ items.length }} 条库存数据。</p>
    </PageState>
  </section>
</template>
