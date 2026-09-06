<script setup lang="ts">
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import { listProducts } from '@/api/products'
import { useListPage } from '@/composables/usePageData'

const { items, loading, error, loadData } = useListPage(listProducts)
</script>

<template>
  <section class="product-list-page">
    <PageHeader title="产品管理" description="产品和产品分类占位页面。" />
    <PageContext />
    <PageState :loading="loading" :error="error" :empty="items.length === 0" @retry="loadData">
      <p class="product-list-page__placeholder">已加载 {{ items.length }} 条产品数据。</p>
    </PageState>
  </section>
</template>
