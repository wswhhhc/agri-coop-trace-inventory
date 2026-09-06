<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { listWarehouses } from '@/api/warehouses'
import { getApiErrorMessage } from '@/utils/api-error'
import { getDefaultDashboardDateRange } from '@/utils/dashboard-format'
import type { DashboardQueryParams } from '@/types/dashboard'
import type { WarehouseSummary } from '@/types/resources'

defineProps<{
  loading?: boolean
}>()

const emit = defineEmits<{
  search: [params: DashboardQueryParams]
}>()

const defaultRange = getDefaultDashboardDateRange()
const startDate = ref(defaultRange.startDate)
const endDate = ref(defaultRange.endDate)
const warehouseId = ref('')
const warehouses = ref<WarehouseSummary[]>([])
const warehouseLoading = ref(false)
const warehouseError = ref('')
const validationError = ref('')

function dateToNumber(value: string): number {
  const [year, month, day] = value.split('-').map(Number)
  return Date.UTC(year, month - 1, day)
}

function validateDateRange(): boolean {
  if (!startDate.value || !endDate.value) {
    validationError.value = '请选择开始日期和结束日期'
    return false
  }

  const difference = dateToNumber(endDate.value) - dateToNumber(startDate.value)
  if (difference < 0) {
    validationError.value = '开始日期不能晚于结束日期'
    return false
  }
  if (difference / (24 * 60 * 60 * 1000) > 365) {
    validationError.value = '查询时间范围不能超过 366 天'
    return false
  }

  validationError.value = ''
  return true
}

function submit(): void {
  if (!validateDateRange()) return

  emit('search', {
    startDate: startDate.value,
    endDate: endDate.value,
    ...(warehouseId.value ? { warehouseId: warehouseId.value } : {}),
  })
}

function reset(): void {
  const range = getDefaultDashboardDateRange()
  startDate.value = range.startDate
  endDate.value = range.endDate
  warehouseId.value = ''
  validationError.value = ''
  submit()
}

async function loadWarehouses(): Promise<void> {
  warehouseLoading.value = true
  warehouseError.value = ''
  try {
    warehouses.value = await listWarehouses()
  } catch (reason) {
    warehouseError.value = getApiErrorMessage(reason, '仓库列表加载失败，可稍后重试')
  } finally {
    warehouseLoading.value = false
  }
}

onMounted(loadWarehouses)
</script>

<template>
  <form class="dashboard-filters" @submit.prevent="submit">
    <div class="dashboard-filters__field">
      <label for="dashboard-start-date">开始日期</label>
      <input id="dashboard-start-date" v-model="startDate" type="date" />
    </div>
    <div class="dashboard-filters__field">
      <label for="dashboard-end-date">结束日期</label>
      <input id="dashboard-end-date" v-model="endDate" type="date" />
    </div>
    <div class="dashboard-filters__field">
      <label for="dashboard-warehouse">仓库</label>
      <select id="dashboard-warehouse" v-model="warehouseId" :disabled="warehouseLoading">
        <option value="">全部可访问仓库</option>
        <option v-for="warehouse in warehouses" :key="warehouse.id" :value="warehouse.id">
          {{ warehouse.name }}（{{ warehouse.code }}）
        </option>
      </select>
      <small v-if="warehouseError" class="dashboard-filters__warehouse-error">{{ warehouseError }}</small>
    </div>
    <div class="dashboard-filters__actions">
      <button type="submit" :disabled="loading">查询</button>
      <button type="button" :disabled="loading" @click="reset">重置</button>
    </div>
    <p v-if="validationError" class="dashboard-filters__validation-error" role="alert">
      {{ validationError }}
    </p>
  </form>
</template>

<style scoped>
.dashboard-filters {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr)) auto;
  align-items: end;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  background: var(--color-surface-muted);
}

.dashboard-filters__field {
  display: grid;
  gap: var(--space-1);
}

.dashboard-filters__field label {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.dashboard-filters__field small,
.dashboard-filters__validation-error {
  color: var(--color-danger);
  font-size: var(--font-size-xs);
}

.dashboard-filters__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.dashboard-filters__actions button:last-child {
  border-color: var(--color-border-strong);
  background: transparent;
  color: var(--color-text-secondary);
}

.dashboard-filters__validation-error {
  grid-column: 1 / -1;
  margin: 0;
}

@media (max-width: 48rem) {
  .dashboard-filters {
    grid-template-columns: 1fr;
  }

  .dashboard-filters__actions {
    justify-content: stretch;
  }

  .dashboard-filters__actions button {
    flex: 1;
  }
}
</style>
