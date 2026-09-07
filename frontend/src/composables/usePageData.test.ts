import { createApp, defineComponent, h, isRef } from 'vue'
import { describe, expect, it, vi } from 'vitest'

import { usePageData, usePaginatedList } from './usePageData'

describe('usePageData', () => {
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
})
