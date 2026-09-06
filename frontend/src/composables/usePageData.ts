import { onMounted, ref } from 'vue'

import { getApiErrorMessage } from '@/utils/api-error'

export function usePageData<T>(loader: () => Promise<T>, initialValue: T) {
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

  return { data, loading, error, loadData }
}

export function useListPage<T>(loader: () => Promise<T[]>) {
  const state = usePageData(loader, [] as T[])
  return {
    items: state.data,
    loading: state.loading,
    error: state.error,
    loadData: state.loadData,
  }
}
