<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import { getBatch, updateBatch, type BatchStatus } from '@/api/batches'
import QualityInspectionPanel from '@/components/batches/QualityInspectionPanel.vue'
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import { usePageData } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import { getApiErrorMessage } from '@/utils/api-error'

const route = useRoute()
const batchId = String(route.params.batchId)
const { data, loading, error, loadData } = usePageData(() => getBatch(batchId), null)
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
  </section>
</template>
