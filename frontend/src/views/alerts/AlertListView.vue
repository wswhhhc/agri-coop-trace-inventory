<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import { listAlertRules, updateAlertRule } from '@/api/alerts'
import type { AlertRuleUpdatePayload } from '@/api/alerts'
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import { useListPage } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import { getApiErrorMessage } from '@/utils/api-error'

const { items, loading, error, loadData } = useListPage(listAlertRules)
const authStore = useAuthStore()
const canEditRules = computed(
  () => authStore.role === 'COOPERATIVE_ADMIN' && authStore.hasPermission('alert:read'),
)
const editingRuleId = ref<string | null>(null)
const submitting = ref(false)
const formError = ref('')
const successMessage = ref('')
const editForm = reactive({
  thresholdQuantity: '',
  thresholdDays: '',
  turnoverDays: '',
  severity: 'MEDIUM',
  isEnabled: true,
})
const severities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

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
