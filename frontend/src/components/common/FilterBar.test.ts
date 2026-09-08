import { createApp, defineComponent, h } from 'vue'
import { describe, expect, it, vi } from 'vitest'

import FilterBar from './FilterBar.vue'

describe('FilterBar', () => {
  it('renders shared actions and emits submit and reset events', () => {
    const root = document.createElement('div')
    const submit = vi.fn()
    const reset = vi.fn()
    const app = createApp(
      defineComponent({
        setup() {
          return () =>
            h(
              FilterBar,
              { onSubmit: submit, onReset: reset },
              { default: () => h('label', { for: 'keyword' }, '关键字') },
            )
        },
      }),
    )

    app.mount(root)

    const form = root.querySelector('form') as HTMLFormElement | null
    expect(form?.classList.contains('filter-bar')).toBe(true)
    expect(form?.textContent).toContain('关键字')
    expect(form?.textContent).toContain('查询')
    expect(form?.textContent).toContain('重置')

    form?.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
    form?.querySelector('button[type="button"]')?.dispatchEvent(new MouseEvent('click', { bubbles: true }))

    expect(submit).toHaveBeenCalledOnce()
    expect(reset).toHaveBeenCalledOnce()

    app.unmount()
    root.remove()
  })

  it('can hide the reset action', () => {
    const root = document.createElement('div')
    const app = createApp(
      defineComponent({
        setup() {
          return () => h(FilterBar, { showReset: false })
        },
      }),
    )

    app.mount(root)

    expect(root.querySelector('button[type="button"]')).toBeNull()

    app.unmount()
    root.remove()
  })
})
