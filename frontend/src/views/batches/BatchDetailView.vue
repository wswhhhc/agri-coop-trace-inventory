<script setup lang="ts">
import { useRoute } from 'vue-router'

import { getBatch } from '@/api/batches'
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import { usePageData } from '@/composables/usePageData'

const route = useRoute()
const batchId = String(route.params.batchId)
const { data, loading, error, loadData } = usePageData(() => getBatch(batchId), null)
</script>

<template>
  <section class="batch-detail-page">
    <PageHeader title="批次详情" description="查看批次基础信息和服务端生成的追溯码。" />
    <PageContext />
    <PageState
      :loading="loading"
      :error="error"
      :empty="!data"
      empty-message="未找到批次"
      @retry="loadData"
    >
      <dl>
        <div><dt>批次编号</dt><dd>{{ data?.batchNo }}</dd></div>
        <div><dt>追溯码</dt><dd>{{ data?.traceCode }}</dd></div>
        <div><dt>产品 ID</dt><dd>{{ data?.productId }}</dd></div>
        <div><dt>产地</dt><dd>{{ data?.origin }}</dd></div>
        <div><dt>生产日期</dt><dd>{{ data?.productionDate }}</dd></div>
        <div><dt>到期日期</dt><dd>{{ data?.expiryDate }}</dd></div>
        <div><dt>负责人</dt><dd>{{ data?.responsiblePerson || '—' }}</dd></div>
        <div><dt>状态</dt><dd>{{ data?.status }}</dd></div>
      </dl>
    </PageState>
  </section>
</template>
