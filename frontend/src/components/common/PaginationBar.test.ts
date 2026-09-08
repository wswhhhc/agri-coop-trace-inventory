import { createApp, defineComponent, h, nextTick, ref } from 'vue'
import { describe, expect, it } from 'vitest'

import PaginationBar from './PaginationBar.vue'

function mountPagination(props: Record<string, unknown>) {
  const root = document.createElement('div')
  const changes = ref<number[]>([])
  const app = createApp(
    defineComponent({
      setup() {
        return () =>
          h(PaginationBar, {
            ...props,
            onChange: (page: number) => changes.value.push(page),
          })
      },
    }),
  )
  app.mount(root)
  return { app, root, changes }
}

function click(element: Element | null): void {
  if (!element) throw new Error('找不到待点击元素')
  element.dispatchEvent(new MouseEvent('click', { bubbles: true }))
}

function setInputValue(element: HTMLInputElement | null, value: string): void {
  if (!element) throw new Error('找不到待输入元素')
  element.value = value
  element.dispatchEvent(new Event('input', { bubbles: true }))
}

function submit(element: Element | null): void {
  if (!element) throw new Error('找不到待提交表单')
  element.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
}

describe('PaginationBar', () => {
  it('shows all page numbers when there are no more than five pages', () => {
    const { app, root } = mountPagination({
      page: 1,
      totalPages: 5,
      totalItems: 50,
      pageSize: 10,
    })

    expect([...root.querySelectorAll('.pagination-bar__page')].map((item) => item.textContent?.trim())).toEqual([
      '1',
      '2',
      '3',
      '4',
      '5',
    ])
    expect(root.querySelectorAll('.pagination-bar__ellipsis')).toHaveLength(0)

    app.unmount()
  })

  it('collapses long page ranges and opens a two-row page picker', async () => {
    const { app, root, changes } = mountPagination({
      page: 1,
      totalPages: 99,
      totalItems: 990,
      pageSize: 10,
    })

    expect([...root.querySelectorAll('.pagination-bar__page')].map((item) => item.textContent?.trim())).toEqual([
      '1',
      '2',
      '3',
      '99',
    ])
    expect(root.querySelectorAll('.pagination-bar__ellipsis')).toHaveLength(1)

    click(root.querySelector('.pagination-bar__ellipsis'))
    await nextTick()

    expect(root.querySelectorAll('.pagination-bar__picker-page')).toHaveLength(10)
    expect(root.querySelector('.pagination-bar__picker-grid')?.classList.contains('pagination-bar__picker-grid--five-columns')).toBe(true)

    click(root.querySelector('.pagination-bar__picker-page:last-child'))
    await nextTick()
    expect(changes.value).toEqual([10])
    expect(root.querySelector('.pagination-bar__picker')).toBeNull()

    app.unmount()
  })

  it('supports moving between picker groups and keeps the current middle page visible', async () => {
    const { app, root } = mountPagination({
      page: 50,
      totalPages: 99,
      totalItems: 990,
      pageSize: 10,
    })

    expect(root.querySelectorAll('.pagination-bar__ellipsis')).toHaveLength(2)
    expect(root.querySelector('.pagination-bar__page--active')?.textContent?.trim()).toBe('50')

    click(root.querySelector('.pagination-bar__ellipsis'))
    await nextTick()
    click(root.querySelector('[aria-label="下一组页码"]'))
    await nextTick()

    const pickerPages = [...root.querySelectorAll('.pagination-bar__picker-page')].map((item) => item.textContent?.trim())
    expect(pickerPages).toEqual(['51', '52', '53', '54', '55', '56', '57', '58', '59', '60'])

    app.unmount()
  })

  it('closes the picker when the active ellipsis is clicked again', async () => {
    const { app, root } = mountPagination({
      page: 1,
      totalPages: 99,
      totalItems: 990,
      pageSize: 10,
    })

    const ellipsis = root.querySelector('.pagination-bar__ellipsis')
    click(ellipsis)
    await nextTick()
    expect(root.querySelector('.pagination-bar__picker')).not.toBeNull()

    click(ellipsis)
    await nextTick()
    expect(root.querySelector('.pagination-bar__picker')).toBeNull()

    app.unmount()
  })

  it('jumps to a valid page from the page input', async () => {
    const { app, root, changes } = mountPagination({
      page: 1,
      totalPages: 99,
      totalItems: 990,
      pageSize: 10,
    })

    click(root.querySelector('.pagination-bar__ellipsis'))
    await nextTick()
    setInputValue(root.querySelector('[aria-label="输入页码"]'), '42')
    await nextTick()

    submit(root.querySelector('.pagination-bar__jump-form'))
    await nextTick()

    expect(changes.value).toEqual([42])
    expect(root.querySelector('.pagination-bar__picker')).toBeNull()

    app.unmount()
  })
})
