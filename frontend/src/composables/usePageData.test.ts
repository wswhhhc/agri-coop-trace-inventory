import { createApp, defineComponent, h, isRef } from 'vue'
import { describe, expect, it, vi } from 'vitest'

import {
  cleanQueryParams,
  getPagePlaceholderCount,
  useFilteredPaginatedList,
  usePageData,
  usePaginatedList,
} from './usePageData'

describe('usePageData', () => {
  it('calculates placeholder rows needed to keep a paginated table at page size', () => {
    expect(getPagePlaceholderCount(10, 10)).toBe(0)
    expect(getPagePlaceholderCount(10, 6)).toBe(4)
    expect(getPagePlaceholderCount(10, 12)).toBe(0)
  })

  it('removes empty query values without dropping false or zero', () => {
    expect(
      cleanQueryParams({ keyword: '  ', categoryId: null, isActive: false, page: 0 }),
    ).toEqual({ isActive: false, page: 0 })
  })

  it('keeps page data reactive when rendered from the composable state', async () => {
    const loader = vi.fn().mockResolvedValue({ id: 'batch-1' })
    const root = document.createElement('div')
    const app = createApp(
      defineComponent({
        setup() {
          const state = usePageData(loader, null as { id: string } | null)
          return () => h('div', state.data?.id ?? 'empty')
        },
      }),
    )

    app.mount(root)

    await vi.waitFor(() => expect(root.textContent).toBe('batch-1'))

    app.unmount()
  })

  it('exposes nested page state as plain reactive properties', async () => {
    const loader = vi.fn().mockResolvedValue([{ id: 'product-1' }])
    let state: ReturnType<typeof usePageData> | undefined
    const app = createApp(
      defineComponent({
        setup() {
          state = usePageData(loader, [] as Array<{ id: string }>)
          return () => h('div')
        },
      }),
    )

    app.mount(document.createElement('div'))

    await vi.waitFor(() => expect(state?.data).toEqual([{ id: 'product-1' }]))
    expect(isRef(state?.data)).toBe(false)
    expect(isRef(state?.loading)).toBe(false)
    expect(isRef(state?.error)).toBe(false)

    app.unmount()
  })

  it('loads pages with a shared page size and exposes pagination controls', async () => {
    const loader = vi.fn().mockResolvedValue({
      data: [{ id: 'product-1' }],
      pagination: { page: 1, pageSize: 10, totalItems: 11, totalPages: 2 },
    })
    let state: ReturnType<typeof usePaginatedList> | undefined
    const app = createApp(
      defineComponent({
        setup() {
          state = usePaginatedList(loader)
          return () => h('div')
        },
      }),
    )

    app.mount(document.createElement('div'))

    await vi.waitFor(() => expect(state?.items).toEqual([{ id: 'product-1' }]))
    expect(loader).toHaveBeenCalledWith({ page: 1, pageSize: 10 })
    expect(state?.pagination).toEqual({ page: 1, pageSize: 10, totalItems: 11, totalPages: 2 })

    loader.mockResolvedValueOnce({
      data: [{ id: 'product-2' }],
      pagination: { page: 2, pageSize: 10, totalItems: 11, totalPages: 2 },
    })
    await state?.goToPage(2)

    expect(loader).toHaveBeenLastCalledWith({ page: 2, pageSize: 10 })
    expect(state?.items).toEqual([{ id: 'product-2' }])

    app.unmount()
  })

  it('can defer the initial load for permission-gated lists', async () => {
    const loader = vi.fn().mockResolvedValue({
      data: [{ id: 'rule-1' }],
      pagination: { page: 1, pageSize: 10, totalItems: 1, totalPages: 1 },
    })
    let state: ReturnType<typeof usePaginatedList> | undefined
    const app = createApp(
      defineComponent({
        setup() {
          state = usePaginatedList(loader, 10, { autoLoad: false })
          return () => h('div')
        },
      }),
    )

    app.mount(document.createElement('div'))
    await Promise.resolve()
    expect(loader).not.toHaveBeenCalled()

    await state?.loadData()
    expect(loader).toHaveBeenCalledWith({ page: 1, pageSize: 10 })

    app.unmount()
  })

  it('loads filtered pages from page one and resets the shared filters', async () => {
    const loader = vi.fn().mockResolvedValue({
      data: [{ id: 'product-1' }],
      pagination: { page: 1, pageSize: 10, totalItems: 1, totalPages: 1 },
    })
    let state: ReturnType<typeof useFilteredPaginatedList> | undefined
    const app = createApp(
      defineComponent({
        setup() {
          state = useFilteredPaginatedList(loader, {
            keyword: '',
            isActive: undefined as boolean | undefined,
          })
          return () => h('div')
        },
      }),
    )

    app.mount(document.createElement('div'))
    await vi.waitFor(() => expect(loader).toHaveBeenCalledWith({ page: 1, pageSize: 10 }))
    await vi.waitFor(() => expect(state?.items).toEqual([{ id: 'product-1' }]))

    state!.filters.keyword = '  番茄  '
    state!.filters.isActive = false
    await state!.applyFilters()
    expect(loader).toHaveBeenLastCalledWith({
      page: 1,
      pageSize: 10,
      keyword: '番茄',
      isActive: false,
    })

    await state!.resetFilters()
    expect(loader).toHaveBeenLastCalledWith({ page: 1, pageSize: 10 })
    expect(state!.filters).toEqual({ keyword: '', isActive: undefined })

    app.unmount()
  })
})
