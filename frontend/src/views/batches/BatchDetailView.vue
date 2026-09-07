<script setup lang="ts">
import { computed, reactive, ref, toRefs, watch } from 'vue'
import { useRoute } from 'vue-router'

import { getBatch, updateBatch, type BatchStatus } from '@/api/batches'
import { getPublicQrCodeUrl } from '@/api/public-traceability'
import QualityInspectionPanel from '@/components/batches/QualityInspectionPanel.vue'
import TraceEventTimeline from '@/components/batches/TraceEventTimeline.vue'
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { usePageData } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import { getApiErrorMessage } from '@/utils/api-error'

const route = useRoute()
const batchId = String(route.params.batchId)
const pageState = usePageData(() => getBatch(batchId), null)
const { data, loading, error } = toRefs(pageState)
const { loadData } = pageState
const authStore = useAuthStore()
const canManage = computed(() => authStore.hasPermission('batch:manage'))
const updating = ref(false)
const updateError = ref('')
const successMessage = ref('')
const statusOptions: BatchStatus[] = ['CREATED', 'IN_STOCK', 'DEPLETED', 'BLOCKED', 'EXPIRED']
const form = reactive({
  origin: '',
  expiryDate: '',
  responsiblePerson: '',
  status: 'CREATED' as BatchStatus,
})

function batchStatusTone(value: string): 'success' | 'warning' | 'danger' | 'info' {
  if (value === 'IN_STOCK') return 'success'
  if (value === 'EXPIRED' || value === 'BLOCKED') return 'danger'
  if (value === 'DEPLETED') return 'warning'
  return 'info'
}

watch(data, syncForm)

function syncForm(): void {
  if (!data.value) return
  form.origin = data.value.origin
  form.expiryDate = data.value.expiryDate
  form.responsiblePerson = data.value.responsiblePerson ?? ''
  form.status = data.value.status as BatchStatus
}

async function handleUpdate(): Promise<void> {
  if (!data.value) return
  updating.value = true
  updateError.value = ''
  successMessage.value = ''
  try {
    await updateBatch(batchId, {
      origin: form.origin.trim(),
      expiryDate: form.expiryDate,
      responsiblePerson: form.responsiblePerson.trim() || null,
      status: form.status,
    })
    await loadData()
    syncForm()
    successMessage.value = '批次更新成功。'
  } catch (reason) {
    updateError.value = getApiErrorMessage(reason)
  } finally {
    updating.value = false
  }
}
</script>

<template>
  <section class="batch-detail-page">
    <PageHeader eyebrow="批次档案" title="批次详情" description="查看批次基础信息和服务端生成的追溯码。" />
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
        <div><dt>状态</dt><dd><StatusBadge v-if="data" :label="data.status" :tone="batchStatusTone(data.status)" /></dd></div>
      </dl>
      <section>
        <h2>公开追溯二维码</h2>
        <img
          :src="getPublicQrCodeUrl(data.traceCode)"
          :alt="`批次 ${data.batchNo} 的公开追溯二维码`"
          loading="lazy"
          decoding="async"
          width="180"
          height="180"
        />
        <p><RouterLink :to="{ name: 'public-trace', params: { traceCode: data.traceCode } }">打开公开追溯页</RouterLink></p>
      </section>
      <form v-if="canManage && data" class="batch-edit-form" @submit.prevent="handleUpdate">
        <h2>编辑批次</h2>
        <label>
          产地
          <input v-model="form.origin" name="origin" required maxlength="255" />
        </label>
        <label>
          到期日期
          <input v-model="form.expiryDate" type="date" name="expiryDate" required />
        </label>
        <label>
          负责人
          <input v-model="form.responsiblePerson" name="responsiblePerson" maxlength="50" />
        </label>
        <label>
          状态
          <select v-model="form.status" name="status" required>
            <option v-for="status in statusOptions" :key="status" :value="status">{{ status }}</option>
          </select>
        </label>
        <button type="submit" :disabled="updating">{{ updating ? '保存中…' : '保存' }}</button>
        <p v-if="updateError" role="alert">{{ updateError }}</p>
        <p v-if="successMessage" role="status">{{ successMessage }}</p>
      </form>
    </PageState>
    <QualityInspectionPanel v-if="data" :batch-id="batchId" :can-manage="canManage" />
    <TraceEventTimeline v-if="data" :batch-id="batchId" />
  </section>
</template>

<style scoped>
.batch-detail-page {
  display: grid;
  gap: var(--space-5);
}

.batch-detail-page > .page-state {
  display: grid;
  gap: var(--space-5);
  place-items: stretch;
  text-align: left;
}

.batch-detail-page > .page-state > dl {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-3);
  margin: 0;
}

.batch-detail-page > .page-state > dl > div {
  display: grid;
  gap: var(--space-1);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-3);
  background: var(--color-surface-muted);
}

.batch-detail-page > .page-state dt {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.batch-detail-page > .page-state dd {
  margin: 0;
  color: var(--color-text-secondary);
  overflow-wrap: anywhere;
}

.batch-detail-page > .page-state > section {
  display: grid;
  justify-items: start;
  gap: var(--space-3);
  border-top: 1px solid var(--color-border);
  padding-top: var(--space-5);
}

.batch-detail-page > .page-state > section h2 {
  margin-bottom: 0;
  font-size: var(--font-size-lg);
}

.batch-detail-page > .page-state > section img {
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  padding: var(--space-2);
  background: var(--color-white);
}

.batch-edit-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.batch-edit-form h2 {
  grid-column: 1 / -1;
  margin-bottom: 0;
  font-size: var(--font-size-lg);
}

.batch-edit-form > label {
  display: grid;
  gap: var(--space-1);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.batch-edit-form > button {
  justify-self: start;
}

.batch-edit-form > p {
  grid-column: 1 / -1;
  margin: 0;
  padding: var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
}

.batch-edit-form > p[role='alert'] {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.batch-edit-form > p[role='status'] {
  background: var(--color-success-soft);
  color: var(--color-success);
}

@media (max-width: 48rem) {
  .batch-detail-page > .page-state > dl {
    grid-template-columns: 1fr;
  }

  .batch-edit-form {
    grid-template-columns: 1fr;
    padding: var(--space-4);
  }

  .batch-edit-form h2,
  .batch-edit-form > p {
    grid-column: auto;
  }

  .batch-edit-form > button {
    justify-self: stretch;
  }
}
</style>
