import { createApp, defineComponent, h, isRef } from 'vue'
import { describe, expect, it, vi } from 'vitest'

import { usePageData } from './usePageData'

describe('usePageData', () => {
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
})
