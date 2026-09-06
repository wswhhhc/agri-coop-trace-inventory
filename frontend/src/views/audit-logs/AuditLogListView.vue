<script setup lang="ts">
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import { listAuditLogs } from '@/api/audit-logs'
import { useListPage } from '@/composables/usePageData'

const { items, loading, error, loadData } = useListPage(listAuditLogs)
</script>

<template>
  <section class="audit-log-list-page">
    <PageHeader title="操作日志" description="审计日志查询占位页面。" />
    <PageContext />
    <PageState :loading="loading" :error="error" :empty="items.length === 0" @retry="loadData">
      <p class="audit-log-list-page__placeholder">已加载 {{ items.length }} 条操作日志。</p>
    </PageState>
  </section>
</template>
