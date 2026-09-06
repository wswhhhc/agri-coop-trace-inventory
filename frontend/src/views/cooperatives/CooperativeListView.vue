<script setup lang="ts">
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import { listCooperatives } from '@/api/cooperatives'
import { useListPage } from '@/composables/usePageData'

const { items, loading, error, loadData } = useListPage(listCooperatives)
</script>

<template>
  <section class="cooperative-list-page">
    <PageHeader title="合作社管理" description="平台级合作社信息占位页面。" />
    <PageContext />
    <PageState :loading="loading" :error="error" :empty="items.length === 0" @retry="loadData">
      <p class="cooperative-list-page__placeholder">已加载 {{ items.length }} 条合作社数据。</p>
    </PageState>
  </section>
</template>
