<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import {
  getAlert,
  getTask,
  listAlertRulesPage,
  listAlertsPage,
  submitAlertScanTask,
  updateAlert,
  updateAlertRule,
} from '@/api/alerts'
import type { AlertRuleUpdatePayload } from '@/api/alerts'
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import ModalShell from '@/components/common/ModalShell.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TaskProgress from '@/components/common/TaskProgress.vue'
import { usePaginatedList } from '@/composables/usePageData'
import type { AlertDetailSummary, TaskSummary } from '@/types/resources'
import { useAuthStore } from '@/stores/auth'
import { canManageAlertRules } from '@/utils/alerting-permission'
import { getApiErrorMessage } from '@/utils/api-error'

const authStore = useAuthStore()
const canEditRules = computed(
  () => canManageAlertRules(authStore.role, authStore.permissions),
)
const ruleList = usePaginatedList(listAlertRulesPage)
const alertList = usePaginatedList(listAlertsPage)
const canHandleAlerts = computed(() => authStore.hasPermission('alert:handle'))
const editingRuleId = ref<string | null>(null)
const submitting = ref(false)
const formError = ref('')
const successMessage = ref('')
const selectedAlert = ref<AlertDetailSummary | null>(null)
let alertDetailRequestId = 0
const alertDetailLoading = ref(false)
const alertDetailError = ref('')
const handling = ref(false)
const handlingError = ref('')
const handlingForm = reactive({ status: 'RESOLVED', handlingNote: '' })
const alertStatuses = ['PENDING', 'PROCESSING', 'RESOLVED', 'IGNORED']
const canScan = computed(() => ['SYSTEM_ADMIN', 'COOPERATIVE_ADMIN'].includes(authStore.role ?? ''))
const scanSubmitting = ref(false)
const scanError = ref('')
const scanTask = ref<TaskSummary | null>(null)
const editForm = reactive({
  thresholdQuantity: '',
  thresholdDays: '',
  turnoverDays: '',
  severity: 'MEDIUM',
  isEnabled: true,
})
const severities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

function severityTone(value: string): 'success' | 'warning' | 'danger' | 'info' {
  if (value === 'CRITICAL' || value === 'HIGH') return 'danger'
  if (value === 'MEDIUM') return 'warning'
  return 'info'
}

function statusTone(value: string): 'success' | 'warning' | 'danger' | 'info' {
  if (value === 'RESOLVED') return 'success'
  if (value === 'PENDING' || value === 'PROCESSING') return 'warning'
  return 'info'
}

async function loadAlertDetail(alertId: string): Promise<void> {
  const requestId = ++alertDetailRequestId
  alertDetailLoading.value = true
  alertDetailError.value = ''
  try {
    const alert = await getAlert(alertId)
    if (requestId !== alertDetailRequestId) return
    selectedAlert.value = alert
    handlingForm.status = selectedAlert.value.status
    handlingForm.handlingNote = ''
    handlingError.value = ''
  } catch (reason) {
    alertDetailError.value = getApiErrorMessage(reason, '预警详情加载失败')
  } finally {
    alertDetailLoading.value = false
  }
}

function closeAlertDetail(): void {
  alertDetailRequestId += 1
  selectedAlert.value = null
  alertDetailLoading.value = false
  alertDetailError.value = ''
  handlingError.value = ''
}

async function handleAlert(): Promise<void> {
  if (!selectedAlert.value) return
  const requestId = alertDetailRequestId
  handling.value = true
  handlingError.value = ''
  try {
    const updatedAlert = await updateAlert(selectedAlert.value.id, {
      status: handlingForm.status,
      handlingNote: handlingForm.handlingNote.trim() || null,
    })
    if (requestId !== alertDetailRequestId) return
    selectedAlert.value = updatedAlert
    handlingForm.handlingNote = ''
    successMessage.value = '预警处理成功。'
    await alertList.loadData()
  } catch (reason) {
    handlingError.value = getApiErrorMessage(reason, '预警处理失败')
  } finally {
    handling.value = false
  }
}

function beginEdit(rule: (typeof ruleList.items)[number]): void {
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
    await ruleList.loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    submitting.value = false
  }
}

function wait(milliseconds: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds))
}

async function runAlertScan(): Promise<void> {
  scanSubmitting.value = true
  scanError.value = ''
  scanTask.value = null
  try {
    scanTask.value = await submitAlertScanTask()
    for (let attempt = 0; attempt < 20; attempt += 1) {
      if (scanTask.value.status === 'SUCCESS' || scanTask.value.status === 'FAILURE') break
      await wait(1000)
      scanTask.value = await getTask(scanTask.value.id)
    }
    await alertList.loadData()
  } catch (reason) {
    scanError.value = getApiErrorMessage(reason, '预警扫描任务失败')
  } finally {
    scanSubmitting.value = false
  }
}
</script>

<template>
  <section class="alert-list-page">
    <PageHeader eyebrow="风险中心" title="预警规则" description="查看库存、临期和质量预警规则。" />
    <PageContext />
    <button v-if="canScan" type="button" :disabled="scanSubmitting" @click="runAlertScan">
      {{ scanSubmitting ? '扫描中…' : '立即扫描预警' }}
    </button>
    <TaskProgress v-if="scanTask" label="预警扫描任务" :status="scanTask.status" :progress="scanTask.progress" />
    <p v-if="scanTask?.errorMessage" role="alert">{{ scanTask.errorMessage }}</p>
    <p v-if="scanError" role="alert">{{ scanError }}</p>
    <p v-if="formError" role="alert">{{ formError }}</p>
    <p v-if="successMessage" role="status">{{ successMessage }}</p>
    <section v-if="canEditRules" class="alert-rule-list">
      <PageState
        :loading="ruleList.loading"
        :error="ruleList.error"
        :empty="ruleList.items.length === 0"
        @retry="ruleList.loadData"
      >
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
              <th scope="col">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="rule in ruleList.items" :key="rule.id">
              <td>{{ rule.alertType }}</td>
              <td>{{ rule.warehouseId || '全局' }}</td>
              <td>{{ rule.productId || '全局' }}</td>
              <td>{{ rule.thresholdQuantity ?? '—' }}</td>
              <td>{{ rule.thresholdDays ?? '—' }}</td>
              <td>{{ rule.turnoverDays ?? '—' }}</td>
              <td><StatusBadge :label="rule.severity" :tone="severityTone(rule.severity)" /></td>
              <td><StatusBadge :label="rule.isEnabled ? '启用' : '停用'" :tone="rule.isEnabled ? 'success' : 'neutral'" /></td>
              <td><button type="button" @click="beginEdit(rule)">编辑</button></td>
            </tr>
          </tbody>
        </table>
      </PageState>
      <PaginationBar
        :page="ruleList.pagination.page"
        :total-pages="ruleList.pagination.totalPages"
        :total-items="ruleList.pagination.totalItems"
        :page-size="ruleList.pagination.pageSize"
        @change="ruleList.goToPage"
        @page-size-change="ruleList.setPageSize"
      />
    </section>
    <p v-else class="permission-hint" role="status">
      当前账号可查看和处理预警实例，暂无预警规则管理权限。
    </p>

    <section class="alert-instance-list">
      <h2>预警实例</h2>
      <PageState
        :loading="alertList.loading"
        :error="alertList.error"
        :empty="alertList.items.length === 0"
        empty-message="暂无预警实例"
        @retry="alertList.loadData"
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
            <tr v-for="alert in alertList.items" :key="alert.id">
              <td>{{ alert.title }}</td>
              <td>{{ alert.alertType }}</td>
              <td><StatusBadge :label="alert.severity" :tone="severityTone(alert.severity)" /></td>
              <td><StatusBadge :label="alert.status" :tone="statusTone(alert.status)" /></td>
              <td>{{ alert.detectedAt }}</td>
              <td><button type="button" @click="loadAlertDetail(alert.id)">查看详情</button></td>
            </tr>
          </tbody>
        </table>
      </PageState>
      <PaginationBar
        :page="alertList.pagination.page"
        :total-pages="alertList.pagination.totalPages"
        :total-items="alertList.pagination.totalItems"
        :page-size="alertList.pagination.pageSize"
        @change="alertList.goToPage"
        @page-size-change="alertList.setPageSize"
      />
    </section>

    <ModalShell
      :open="alertDetailLoading || Boolean(alertDetailError) || Boolean(selectedAlert)"
      title="预警详情"
      @close="closeAlertDetail"
    >
      <div class="alert-detail">
        <p v-if="alertDetailLoading">详情加载中…</p>
        <p v-else-if="alertDetailError" role="alert">{{ alertDetailError }}</p>
        <dl v-else-if="selectedAlert">
          <div><dt>标题</dt><dd>{{ selectedAlert.title }}</dd></div>
          <div><dt>类型</dt><dd>{{ selectedAlert.alertType }}</dd></div>
          <div><dt>级别</dt><dd><StatusBadge :label="selectedAlert.severity" :tone="severityTone(selectedAlert.severity)" /></dd></div>
          <div><dt>状态</dt><dd><StatusBadge :label="selectedAlert.status" :tone="statusTone(selectedAlert.status)" /></dd></div>
          <div><dt>说明</dt><dd>{{ selectedAlert.message }}</dd></div>
          <div><dt>仓库</dt><dd>{{ selectedAlert.warehouseId || '—' }}</dd></div>
          <div><dt>产品</dt><dd>{{ selectedAlert.productId || '—' }}</dd></div>
          <div><dt>批次</dt><dd>{{ selectedAlert.batchId || '—' }}</dd></div>
          <div><dt>证据</dt><dd><pre>{{ JSON.stringify(selectedAlert.evidence, null, 2) }}</pre></dd></div>
          <div><dt>检测时间</dt><dd>{{ selectedAlert.detectedAt }}</dd></div>
          <div v-if="selectedAlert.handlingLogs.length">
            <dt>处理记录</dt>
            <dd>
              <ul>
                <li v-for="log in selectedAlert.handlingLogs" :key="log.id">
                  {{ log.fromStatus }} → {{ log.toStatus }}：{{ log.comment || '—' }}（{{ log.createdAt }}）
                </li>
              </ul>
            </dd>
          </div>
        </dl>
        <form v-if="canHandleAlerts && selectedAlert" class="alert-handle-form" @submit.prevent="handleAlert">
          <h3>处理预警</h3>
          <label>
            目标状态
            <select v-model="handlingForm.status">
              <option v-for="status in alertStatuses" :key="status" :value="status">{{ status }}</option>
            </select>
          </label>
          <label>
            处理说明
            <textarea v-model="handlingForm.handlingNote" maxlength="500" />
          </label>
          <button type="submit" :disabled="handling">{{ handling ? '提交中…' : '提交处理' }}</button>
          <p v-if="handlingError" role="alert">{{ handlingError }}</p>
        </form>
      </div>
    </ModalShell>

    <ModalShell
      :open="canEditRules && Boolean(editingRuleId)"
      title="编辑预警规则"
      @close="cancelEdit"
    >
      <form class="alert-rule-edit-form" @submit.prevent="handleUpdate">
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
        <div class="alert-rule-edit-form__actions">
          <button type="submit" :disabled="submitting">{{ submitting ? '保存中…' : '保存' }}</button>
          <button type="button" :disabled="submitting" @click="cancelEdit">取消</button>
        </div>
      </form>
    </ModalShell>
  </section>
</template>

<style scoped>
.alert-list-page {
  display: grid;
  gap: var(--space-5);
}

.alert-list-page > .page-state,
.alert-instance-list > .page-state {
  overflow-x: auto;
}

.alert-list-page > .page-state table,
.alert-instance-list > .page-state table {
  min-width: 54rem;
}

.alert-list-page > button {
  justify-self: start;
}

.alert-instance-list {
  display: grid;
  gap: var(--space-3);
}

.alert-instance-list h2 {
  margin-bottom: 0;
  font-size: var(--font-size-lg);
}

.alert-detail {
  display: grid;
  gap: var(--space-4);
}

.alert-detail dl {
  display: grid;
  gap: var(--space-2);
  margin: 0;
}

.alert-detail dl > div {
  display: grid;
  grid-template-columns: minmax(6rem, 0.35fr) minmax(0, 1fr);
  gap: var(--space-4);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: var(--space-2);
}

.alert-detail dt {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.alert-detail dd {
  min-width: 0;
  margin: 0;
  color: var(--color-text-secondary);
  overflow-wrap: anywhere;
}

.alert-handle-form,
.alert-rule-edit-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.alert-handle-form {
  border-top: 1px solid var(--color-border);
  padding-top: var(--space-4);
}

.alert-handle-form h3,
.alert-handle-form > label:nth-of-type(2),
.alert-handle-form > p {
  grid-column: 1 / -1;
}

.alert-handle-form > label,
.alert-rule-edit-form > label {
  display: grid;
  gap: var(--space-1);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.alert-handle-form > button {
  justify-self: start;
}

.alert-rule-edit-form__actions {
  display: flex;
  grid-column: 1 / -1;
  gap: var(--space-2);
}

.alert-handle-form > p[role='alert'],
.alert-rule-edit-form > p[role='alert'] {
  margin: 0;
  color: var(--color-danger);
  font-size: var(--font-size-sm);
}

@media (max-width: 48rem) {
  .alert-detail dl > div {
    grid-template-columns: 1fr;
    gap: var(--space-1);
  }

  .alert-handle-form,
  .alert-rule-edit-form {
    grid-template-columns: 1fr;
  }

  .alert-handle-form h3,
  .alert-handle-form > label:nth-of-type(2),
  .alert-handle-form > p,
  .alert-rule-edit-form__actions {
    grid-column: auto;
  }

  .alert-handle-form > button,
  .alert-rule-edit-form__actions > button {
    justify-self: stretch;
  }

  .alert-rule-edit-form__actions {
    flex-direction: column;
  }
}
</style>
