import { createApp, defineComponent, h, nextTick } from 'vue'
import { describe, expect, it, vi } from 'vitest'

import CreateFormModal from './CreateFormModal.vue'

describe('CreateFormModal', () => {
  it('renders business fields inside a shared modal and emits submit and close events', async () => {
    const root = document.createElement('div')
    const submit = vi.fn()
    const close = vi.fn()
    const app = createApp(
      defineComponent({
        setup() {
          return () =>
            h(
              CreateFormModal,
              {
                open: true,
                title: '创建仓库',
                submitting: false,
                onSubmit: submit,
                onClose: close,
              },
              { default: () => h('label', { for: 'warehouse-name' }, '仓库名称') },
            )
        },
      }),
    )

    app.mount(root)

    const dialog = document.body.querySelector('[role="dialog"]') as HTMLElement | null
    expect(dialog?.textContent).toContain('创建仓库')
    expect(dialog?.textContent).toContain('仓库名称')

    dialog?.querySelector('form')?.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
    expect(submit).toHaveBeenCalledOnce()

    const cancelButton = Array.from(dialog?.querySelectorAll('button') ?? []).find(
      (button) => button.textContent === '取消',
    )
    cancelButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    await nextTick()
    expect(close).toHaveBeenCalledOnce()

    app.unmount()
    root.remove()
  })

  it('keeps the cancel action disabled while submitting and shows errors', () => {
    const root = document.createElement('div')
    const app = createApp(
      defineComponent({
        setup() {
          return () =>
            h(
              CreateFormModal,
              {
                open: true,
                title: '创建用户',
                submitting: true,
                error: '用户名已存在',
              },
              { default: () => h('input', { name: 'username' }) },
            )
        },
      }),
    )

    app.mount(root)

    const dialog = document.body.querySelector('[role="dialog"]') as HTMLElement | null
    expect(dialog?.querySelector('[role="alert"]')?.textContent).toBe('用户名已存在')
    const buttons = Array.from(dialog?.querySelectorAll('button') ?? [])
    expect(buttons.find((button) => button.textContent === '取消')?.hasAttribute('disabled')).toBe(true)
    expect(buttons.find((button) => button.textContent?.includes('提交中'))).toBeTruthy()

    app.unmount()
    root.remove()
  })

  it('can disable submit while related options are loading without showing a submitting label', () => {
    const root = document.createElement('div')
    const app = createApp(
      defineComponent({
        setup() {
          return () =>
            h(
              CreateFormModal,
              {
                open: true,
                title: '创建产品',
                submitDisabled: true,
              },
              { default: () => h('input', { name: 'name' }) },
            )
        },
      }),
    )

    app.mount(root)

    const dialog = document.body.querySelector('[role="dialog"]') as HTMLElement | null
    const submitButton = Array.from(dialog?.querySelectorAll('button') ?? []).find(
      (button) => button.type === 'submit',
    )
    expect(submitButton?.disabled).toBe(true)
    expect(submitButton?.textContent).toBe('创建')

    app.unmount()
    root.remove()
  })
})
