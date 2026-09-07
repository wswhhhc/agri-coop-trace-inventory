import { onMounted, reactive, ref } from 'vue'

import {
  getAlertDistribution,
  getDashboardSummary,
  getForecastComparison,
  getProductRanking,
} from '@/api/dashboard'
import { getApiErrorMessage } from '@/utils/api-error'
import { getDefaultDashboardDateRange } from '@/utils/dashboard-format'
import type {
  AlertDistribution,
  DashboardQueryParams,
  DashboardSummary,
  ForecastComparisonItem,
  ProductRankingItem,
} from '@/types/dashboard'

export type DashboardModule =
  | 'summary'
  | 'alertDistribution'
  | 'productRanking'
  | 'forecastComparison'

export type DashboardLoadingState = Record<DashboardModule, boolean>
export type DashboardErrorState = Record<DashboardModule, string>

export interface UseDashboardOptions {
  canReadForecastComparison?: boolean
}

export function useDashboard(options: UseDashboardOptions = {}) {
  const dashboardModules: DashboardModule[] = [
    'summary',
    'alertDistribution',
    'productRanking',
    ...(options.canReadForecastComparison === false ? [] : ['forecastComparison' as const]),
  ]
  const defaultRange = getDefaultDashboardDateRange()
  const query = ref<DashboardQueryParams>({ ...defaultRange })
  const summary = ref<DashboardSummary | null>(null)
  const alertDistribution = ref<AlertDistribution | null>(null)
  const productRanking = ref<ProductRankingItem[]>([])
  const forecastComparison = ref<ForecastComparisonItem[]>([])
  const loading = reactive<DashboardLoadingState>({
    summary: false,
    alertDistribution: false,
    productRanking: false,
    forecastComparison: false,
  })
  const errors = reactive<DashboardErrorState>({
    summary: '',
    alertDistribution: '',
    productRanking: '',
    forecastComparison: '',
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
      if (module === 'forecastComparison') {
        forecastComparison.value = await getForecastComparison(params)
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
    forecastComparison,
    loading,
    errors,
    loadDashboard,
    retry,
  }
}
