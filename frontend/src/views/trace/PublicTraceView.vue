<script setup lang="ts">
import { useRoute } from 'vue-router'

import { getPublicTrace } from '@/api/public-traceability'
import PageState from '@/components/common/PageState.vue'
import { usePageData } from '@/composables/usePageData'

const route = useRoute()
const traceCode = String(route.params.traceCode)
const { data, loading, error, loadData } = usePageData(() => getPublicTrace(traceCode), null)
</script>

<template>
  <main class="public-trace-page">
    <h1>农产品批次追溯</h1>
    <PageState :loading="loading" :error="error" :empty="!data" empty-message="追溯码无效或已失效" @retry="loadData">
      <template v-if="data">
        <p>追溯码：{{ data.traceCode }}</p>
        <section>
          <h2>产品信息</h2>
          <dl>
            <div><dt>名称</dt><dd>{{ data.product.name }}</dd></div>
            <div><dt>分类</dt><dd>{{ data.product.categoryName }}</dd></div>
            <div><dt>单位</dt><dd>{{ data.product.unit }}</dd></div>
          </dl>
        </section>
        <section>
          <h2>批次信息</h2>
          <dl>
            <div><dt>批次编号</dt><dd>{{ data.batch.batchNo }}</dd></div>
            <div><dt>产地</dt><dd>{{ data.batch.origin }}</dd></div>
            <div><dt>生产日期</dt><dd>{{ data.batch.productionDate }}</dd></div>
            <div><dt>到期日期</dt><dd>{{ data.batch.expiryDate }}</dd></div>
            <div><dt>状态</dt><dd>{{ data.batch.status }}</dd></div>
          </dl>
        </section>
        <section v-if="data.latestInspection">
          <h2>最近质检</h2>
          <p>{{ data.latestInspection.inspectionDate }}，结论：{{ data.latestInspection.conclusion }}</p>
          <ul>
            <li v-for="item in data.latestInspection.items" :key="item.name">
              {{ item.name }}：{{ item.value }}{{ item.unit ? ` ${item.unit}` : '' }}，标准：{{ item.standard }}，{{ item.isQualified ? '合格' : '不合格' }}
            </li>
          </ul>
        </section>
        <section>
          <h2>流转时间线</h2>
          <ol>
            <li v-for="event in data.timeline" :key="`${event.eventType}-${event.occurredAt}`">
              <time :datetime="event.occurredAt">{{ event.occurredAt }}</time>
              <strong>{{ event.title }}</strong>
              <p>{{ event.description }}</p>
            </li>
          </ol>
        </section>
        <p role="note">{{ data.dataNotice }}</p>
      </template>
    </PageState>
  </main>
</template>
