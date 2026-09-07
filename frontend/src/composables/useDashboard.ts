import { onMounted, reactive, ref } from 'vue'

import {
  getAlertDistribution,
  getDashboardSummary,
  getProductRanking,
} from '@/api/dashboard'
import { getApiErrorMessage } from '@/utils/api-error'
import { getDefaultDashboardDateRange } from '@/utils/dashboard-format'
import type {
  AlertDistribution,
  DashboardQueryParams,
  DashboardSummary,
  ProductRankingItem,
} from '@/types/dashboard'

export type DashboardModule = 'summary' | 'alertDistribution' | 'productRanking'

export type DashboardLoadingState = Record<DashboardModule, boolean>
export type DashboardErrorState = Record<DashboardModule, string>

const dashboardModules: DashboardModule[] = [
  'summary',
  'alertDistribution',
  'productRanking',
]

export function useDashboard() {
  const defaultRange = getDefaultDashboardDateRange()
  const query = ref<DashboardQueryParams>({ ...defaultRange })
  const summary = ref<DashboardSummary | null>(null)
  const alertDistribution = ref<AlertDistribution | null>(null)
  const productRanking = ref<ProductRankingItem[]>([])
  const loading = reactive<DashboardLoadingState>({
    summary: false,
    alertDistribution: false,
    productRanking: false,
  })
  const errors = reactive<DashboardErrorState>({
    summary: '',
    alertDistribution: '',
    productRanking: '',
  })

  async function loadModule(module: DashboardModule, params = query.value): Promise<void> {
    loading[module] = true
    errors[module] = ''

    try {
      if (module === 'summary') summary.value = await getDashboardSummary(params)
      if (module === 'alertDistribution') alertDistribution.value = await getAlertDistribution(params)
      if (module === 'productRanking') {
        productRanking.value = await getProductRanking({ ...params, limit: 10 })
      }
    } catch (reason) {
      errors[module] = getApiErrorMessage(reason)
    } finally {
      loading[module] = false
    }
  }

  async function loadDashboard(params: DashboardQueryParams): Promise<void> {
    query.value = { ...params }
    await Promise.all(dashboardModules.map((module) => loadModule(module, query.value)))
  }

  async function retry(module: DashboardModule): Promise<void> {
    await loadModule(module, query.value)
  }

  onMounted(() => loadDashboard(query.value))

  return {
    query,
    summary,
    alertDistribution,
    productRanking,
    loading,
    errors,
    loadDashboard,
    retry,
  }
}
