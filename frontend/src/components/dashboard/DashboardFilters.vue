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
