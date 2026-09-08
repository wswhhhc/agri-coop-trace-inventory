import { createApp, defineComponent, h, nextTick } from 'vue'
import { describe, expect, it } from 'vitest'

import SelectField, { type SelectFieldOption } from './SelectField.vue'

describe('SelectField', () => {
  it('opens a scrollable option list and updates the selected value', async () => {
    const options: SelectFieldOption[] = [
      { value: '', label: '全部批次' },
      ...Array.from({ length: 12 }, (_, index) => ({
        value: `batch-${index + 1}`,
        label: `批次 ${index + 1}`,
      })),
    ]
    let selectedValue = ''
    const root = document.createElement('div')
    const app = createApp(
      defineComponent({
        setup() {
          return () =>
            h(SelectField, {
              modelValue: selectedValue,
              'onUpdate:modelValue': (value: string) => {
                selectedValue = value
              },
              name: 'batchId',
              required: true,
              options,
            })
        },
      }),
    )

    app.mount(root)
    const trigger = root.querySelector('button[aria-haspopup="listbox"]') as HTMLButtonElement
    trigger.click()
    await nextTick()

    const menu = root.querySelector('[role="listbox"]') as HTMLElement | null
    expect(menu).not.toBeNull()
    expect(menu?.classList.contains('select-field__options')).toBe(true)
    expect(menu?.style.maxHeight).toBe('27.5rem')
    expect(root.querySelector('.select-field__validation')).not.toBeNull()

    const option = Array.from(root.querySelectorAll('[role="option"]')).find(
      (item) => item.textContent?.trim() === '批次 3',
    ) as HTMLButtonElement | undefined
    option?.click()
    await nextTick()

    expect(selectedValue).toBe('batch-3')
    expect(root.querySelector('[role="listbox"]')).toBeNull()

    app.unmount()
    root.remove()
  })
})
