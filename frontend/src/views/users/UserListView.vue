<script setup lang="ts">
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import { listUsers } from '@/api/users'
import { useListPage } from '@/composables/usePageData'

const { items, loading, error, loadData } = useListPage(listUsers)
</script>

<template>
  <section class="user-list-page">
    <PageHeader title="用户管理" description="用户列表和授权操作占位页面。" />
    <PageContext />
    <PageState :loading="loading" :error="error" :empty="items.length === 0" @retry="loadData">
      <p class="user-list-page__placeholder">已加载 {{ items.length }} 条用户数据。</p>
    </PageState>
  </section>
</template>
