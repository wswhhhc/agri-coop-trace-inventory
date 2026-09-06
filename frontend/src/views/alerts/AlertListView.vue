<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import { getAlert, listAlertRules, listAlerts, updateAlertRule } from '@/api/alerts'
import type { AlertRuleUpdatePayload } from '@/api/alerts'
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import { useListPage } from '@/composables/usePageData'
import { usePageData } from '@/composables/usePageData'
import type { AlertDetailSummary } from '@/types/resources'
import { useAuthStore } from '@/stores/auth'
import { getApiErrorMessage } from '@/utils/api-error'

const { items, loading, error, loadData } = useListPage(listAlertRules)
const alertState = usePageData(listAlerts, [])
const authStore = useAuthStore()
const canEditRules = computed(
  () => authStore.role === 'COOPERATIVE_ADMIN' && authStore.hasPermission('alert:read'),
)
const editingRuleId = ref<string | null>(null)
const submitting = ref(false)
const formError = ref('')
const successMessage = ref('')
const selectedAlert = ref<AlertDetailSummary | null>(null)
const alertDetailLoading = ref(false)
const alertDetailError = ref('')
const editForm = reactive({
  thresholdQuantity: '',
  thresholdDays: '',
  turnoverDays: '',
  severity: 'MEDIUM',
  isEnabled: true,
})
const severities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

async function loadAlertDetail(alertId: string): Promise<void> {
  alertDetailLoading.value = true
  alertDetailError.value = ''
  try {
    selectedAlert.value = await getAlert(alertId)
  } catch (reason) {
    alertDetailError.value = getApiErrorMessage(reason, '预警详情加载失败')
  } finally {
    alertDetailLoading.value = false
  }
}

function beginEdit(rule: (typeof items.value)[number]): void {
  editingRuleId.value = rule.id
  editForm.thresholdQuantity = rule.thresholdQuantity === null ? '' : String(rule.thresholdQuantity)
  editForm.thresholdDays = rule.thresholdDays === null ? '' : String(rule.thresholdDays)
  editForm.turnoverDays = rule.turnoverDays === null ? '' : String(rule.turnoverDays)
  editForm.severity = rule.severity
  editForm.isEnabled = rule.isEnabled
  formError.value = ''
  successMessage.value = ''
}

function cancelEdit(): void {
  editingRuleId.value = null
  formError.value = ''
}

function optionalNumber(value: string): number | null {
  return value.trim() === '' ? null : Number(value)
}

async function handleUpdate(): Promise<void> {
  if (!editingRuleId.value) return
  const payload: AlertRuleUpdatePayload = {
    thresholdQuantity: optionalNumber(editForm.thresholdQuantity),
    thresholdDays: optionalNumber(editForm.thresholdDays),
    turnoverDays: optionalNumber(editForm.turnoverDays),
    severity: editForm.severity,
    isEnabled: editForm.isEnabled,
  }
  submitting.value = true
  formError.value = ''
  successMessage.value = ''
  try {
    await updateAlertRule(editingRuleId.value, payload)
    cancelEdit()
    successMessage.value = '预警规则更新成功。'
    await loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="alert-list-page">
    <PageHeader title="预警规则" description="查看库存、临期和质量预警规则。" />
    <PageContext />
    <p v-if="formError" role="alert">{{ formError }}</p>
    <p v-if="successMessage" role="status">{{ successMessage }}</p>
    <PageState :loading="loading" :error="error" :empty="items.length === 0" @retry="loadData">
      <table>
        <caption>预警规则列表</caption>
        <thead>
          <tr>
            <th scope="col">类型</th>
            <th scope="col">仓库</th>
            <th scope="col">产品</th>
            <th scope="col">数量阈值</th>
            <th scope="col">天数阈值</th>
            <th scope="col">周转天数</th>
            <th scope="col">级别</th>
            <th scope="col">状态</th>
            <th v-if="canEditRules" scope="col">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="rule in items" :key="rule.id">
            <td>{{ rule.alertType }}</td>
            <td>{{ rule.warehouseId || '全局' }}</td>
            <td>{{ rule.productId || '全局' }}</td>
            <td>{{ rule.thresholdQuantity ?? '—' }}</td>
            <td>{{ rule.thresholdDays ?? '—' }}</td>
            <td>{{ rule.turnoverDays ?? '—' }}</td>
            <td>{{ rule.severity }}</td>
            <td>{{ rule.isEnabled ? '启用' : '停用' }}</td>
            <td v-if="canEditRules">
              <button type="button" @click="beginEdit(rule)">编辑</button>
            </td>
          </tr>
        </tbody>
      </table>
    </PageState>

    <section class="alert-instance-list">
      <h2>预警实例</h2>
      <PageState
        :loading="alertState.loading"
        :error="alertState.error"
        :empty="alertState.data.length === 0"
        empty-message="暂无预警实例"
        @retry="alertState.loadData"
      >
        <table>
          <caption>预警实例列表</caption>
          <thead>
            <tr>
              <th scope="col">标题</th>
              <th scope="col">类型</th>
              <th scope="col">级别</th>
              <th scope="col">状态</th>
              <th scope="col">检测时间</th>
              <th scope="col">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="alert in alertState.data" :key="alert.id">
              <td>{{ alert.title }}</td>
              <td>{{ alert.alertType }}</td>
              <td>{{ alert.severity }}</td>
              <td>{{ alert.status }}</td>
              <td>{{ alert.detectedAt }}</td>
              <td><button type="button" @click="loadAlertDetail(alert.id)">查看详情</button></td>
            </tr>
          </tbody>
        </table>
      </PageState>
    </section>

    <aside v-if="alertDetailLoading || alertDetailError || selectedAlert" class="alert-detail">
      <h2>预警详情</h2>
      <p v-if="alertDetailLoading">详情加载中…</p>
      <p v-else-if="alertDetailError" role="alert">{{ alertDetailError }}</p>
      <dl v-else-if="selectedAlert">
        <div><dt>标题</dt><dd>{{ selectedAlert.title }}</dd></div>
        <div><dt>类型</dt><dd>{{ selectedAlert.alertType }}</dd></div>
        <div><dt>级别</dt><dd>{{ selectedAlert.severity }}</dd></div>
        <div><dt>状态</dt><dd>{{ selectedAlert.status }}</dd></div>
        <div><dt>说明</dt><dd>{{ selectedAlert.message }}</dd></div>
        <div><dt>仓库</dt><dd>{{ selectedAlert.warehouseId || '—' }}</dd></div>
        <div><dt>产品</dt><dd>{{ selectedAlert.productId || '—' }}</dd></div>
        <div><dt>批次</dt><dd>{{ selectedAlert.batchId || '—' }}</dd></div>
        <div><dt>证据</dt><dd><pre>{{ JSON.stringify(selectedAlert.evidence, null, 2) }}</pre></dd></div>
        <div><dt>检测时间</dt><dd>{{ selectedAlert.detectedAt }}</dd></div>
      </dl>
    </aside>

    <form v-if="canEditRules && editingRuleId" class="alert-rule-edit-form" @submit.prevent="handleUpdate">
      <h2>编辑预警规则</h2>
      <label>
        数量阈值
        <input v-model="editForm.thresholdQuantity" type="number" min="0" step="0.001" />
      </label>
      <label>
        天数阈值
        <input v-model="editForm.thresholdDays" type="number" min="0" step="1" />
      </label>
      <label>
        周转天数
        <input v-model="editForm.turnoverDays" type="number" min="0" step="1" />
      </label>
      <label>
        级别
        <select v-model="editForm.severity">
          <option v-for="severity in severities" :key="severity" :value="severity">{{ severity }}</option>
        </select>
      </label>
      <label>
        <input v-model="editForm.isEnabled" type="checkbox" />
        启用
      </label>
      <button type="submit" :disabled="submitting">{{ submitting ? '保存中…' : '保存' }}</button>
      <button type="button" :disabled="submitting" @click="cancelEdit">取消</button>
    </form>
  </section>
</template>
