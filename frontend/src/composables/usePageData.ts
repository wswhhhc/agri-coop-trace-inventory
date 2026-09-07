import { onMounted, reactive, ref, toRef } from 'vue'

import { getApiErrorMessage } from '@/utils/api-error'

export interface PageDataState<T> {
  data: T
  loading: boolean
  error: string
  loadData: () => Promise<void>
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
