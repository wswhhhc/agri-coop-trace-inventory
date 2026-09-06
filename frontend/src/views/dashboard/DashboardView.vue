<script setup lang="ts">
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import { getDashboardSummary } from '@/api/dashboard'
import { usePageData } from '@/composables/usePageData'
import type { DashboardSummary } from '@/types/resources'

const { data, loading, error, loadData } = usePageData<DashboardSummary | null>(
  getDashboardSummary,
  null,
)
</script>

<template>
  <section class="dashboard-page">
    <PageHeader title="系统首页" description="显示当前账号可访问的数据概览。" />
    <PageContext />
    <PageState :loading="loading" :error="error" @retry="loadData">
      <section class="dashboard-page__placeholder" aria-labelledby="dashboard-summary-title">
        <h2 id="dashboard-summary-title">数据概览占位</h2>
        <p v-if="data">首页汇总接口已返回当前范围数据。</p>
        <dl v-if="data" class="dashboard-page__summary">
          <div>
            <dt>产品数</dt>
            <dd>{{ data.productCount }}</dd>
          </div>
          <div>
            <dt>批次数</dt>
            <dd>{{ data.batchCount }}</dd>
          </div>
          <div>
            <dt>待处理预警</dt>
            <dd>{{ data.pendingAlertCount }}</dd>
          </div>
        </dl>
      </section>
    </PageState>
  </section>
</template>
