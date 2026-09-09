import { onMounted, reactive, ref, toRef } from 'vue'

import type { ListResponse, PaginationMeta } from '@/types/api'
import { getApiErrorMessage } from '@/utils/api-error'

export interface PageDataState<T> {
  data: T
  loading: boolean
  error: string
  loadData: () => Promise<void>
}

export interface PaginationQuery {
  page: number
  pageSize: number
}

export interface PaginatedListState<T> {
  items: T[]
  pagination: PaginationMeta
  loading: boolean
  error: string
  loadData: (page?: number, pageSize?: number) => Promise<void>
  goToPage: (page: number) => Promise<void>
  setPageSize: (pageSize: number) => Promise<void>
}

export interface PaginatedListOptions {
  autoLoad?: boolean
}

export type QueryParamValue = string | number | boolean | null | undefined

export interface FilteredPaginatedListState<
  T,
  F extends Record<string, QueryParamValue>,
> extends PaginatedListState<T> {
  filters: F
  applyFilters: () => Promise<void>
  resetFilters: () => Promise<void>
}

export function cleanQueryParams<T extends Record<string, QueryParamValue>>(
  params: T,
): Partial<T> {
  return Object.fromEntries(
    Object.entries(params).flatMap(([key, value]) => {
      if (value === null || value === undefined) return []
      if (typeof value === 'string') {
        const trimmedValue = value.trim()
        return trimmedValue ? [[key, trimmedValue]] : []
      }
      return [[key, value]]
    }),
  ) as Partial<T>
}

export function getPagePlaceholderCount(pageSize: number, itemCount: number): number {
  return Math.max(0, pageSize - itemCount)
}

export function usePageData<T>(loader: () => Promise<T>, initialValue: T): PageDataState<T> {
  const data = ref<T>(initialValue)
  const loading = ref(false)
  const error = ref('')

  async function loadData(): Promise<void> {
    loading.value = true
    error.value = ''
    try {
      data.value = await loader()
    } catch (reason) {
      error.value = getApiErrorMessage(reason)
    } finally {
      loading.value = false
    }
  }

  onMounted(loadData)

  // reactive 会在对象属性访问时自动解包 ref，避免 `pageState.loading` 作为
  // 子组件 prop 时把 RefImpl 传进去；useListPage 再把列表字段恢复为 ref。
  return reactive({ data, loading, error, loadData }) as PageDataState<T>
}

export function useListPage<T>(loader: () => Promise<T[]>) {
  const state = usePageData(loader, [] as T[])
  return {
    items: toRef(state, 'data'),
    loading: toRef(state, 'loading'),
    error: toRef(state, 'error'),
    loadData: state.loadData,
  }
}

export function usePaginatedList<T>(
  loader: (params: PaginationQuery) => Promise<ListResponse<T>>,
  initialPageSize = 10,
  options: PaginatedListOptions = {},
): PaginatedListState<T> {
  const items = ref<T[]>([])
  const pagination = ref<PaginationMeta>({
    page: 1,
    pageSize: initialPageSize,
    totalItems: 0,
    totalPages: 0,
  })
  const loading = ref(false)
  const error = ref('')

  async function loadData(
    page = pagination.value.page,
    pageSize = pagination.value.pageSize,
  ): Promise<void> {
    loading.value = true
    error.value = ''
    try {
      const response = await loader({ page, pageSize })
      items.value = response.data
      pagination.value = response.pagination
    } catch (reason) {
      error.value = getApiErrorMessage(reason)
    } finally {
      loading.value = false
    }
  }

  async function goToPage(page: number): Promise<void> {
    const totalPages = pagination.value.totalPages
    if (page < 1 || (totalPages > 0 && page > totalPages) || page === pagination.value.page) {
      return
    }
    await loadData(page)
  }

  async function setPageSize(pageSize: number): Promise<void> {
    if (pageSize < 1 || pageSize === pagination.value.pageSize) {
      return
    }
    await loadData(1, pageSize)
  }

  if (options.autoLoad ?? true) {
    onMounted(() => void loadData(1, initialPageSize))
  }

  return reactive({ items, pagination, loading, error, loadData, goToPage, setPageSize }) as PaginatedListState<T>
}

export function useFilteredPaginatedList<
  T,
  F extends Record<string, QueryParamValue>,
>(
  loader: (params: PaginationQuery & Partial<F>) => Promise<ListResponse<T>>,
  initialFilters: F,
  initialPageSize = 10,
): FilteredPaginatedListState<T, F> {
  const filters = reactive({ ...initialFilters }) as F
  const list = usePaginatedList(
    (pagination) => loader({ ...pagination, ...cleanQueryParams(filters) }),
    initialPageSize,
  )

  async function applyFilters(): Promise<void> {
    await list.loadData(1)
  }

  async function resetFilters(): Promise<void> {
    Object.assign(filters, initialFilters)
    await list.loadData(1)
  }

  return reactive({
    items: toRef(list, 'items'),
    pagination: toRef(list, 'pagination'),
    loading: toRef(list, 'loading'),
    error: toRef(list, 'error'),
    loadData: list.loadData,
    goToPage: list.goToPage,
    setPageSize: list.setPageSize,
    filters,
    applyFilters,
    resetFilters,
  }) as FilteredPaginatedListState<T, F>
}
