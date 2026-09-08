import { createApp, defineComponent, h } from 'vue'
import { describe, expect, it, vi } from 'vitest'

import ModalShell from './ModalShell.vue'

describe('ModalShell', () => {
  it('renders the dialog in body and closes when Escape is pressed', () => {
    const root = document.createElement('div')
    const close = vi.fn()
    const app = createApp(
      defineComponent({
        setup() {
          return () =>
            h(
              ModalShell,
              { open: true, title: '编辑预警规则', onClose: close },
              { default: () => h('p', '表单内容') },
            )
        },
      }),
    )

    app.mount(root)

    const dialog = document.body.querySelector('[role="dialog"]') as HTMLElement | null
    expect(root.querySelector('[role="dialog"]')).toBeNull()
    expect(dialog).not.toBeNull()
    expect(dialog?.getAttribute('aria-modal')).toBe('true')
    expect(dialog?.textContent).toContain('表单内容')

    dialog?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))
    expect(close).toHaveBeenCalledOnce()

    app.unmount()
    root.remove()
  })
})
