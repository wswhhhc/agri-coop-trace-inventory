import { createApp, defineComponent, h, ref } from 'vue'
import { describe, expect, it } from 'vitest'

import PageState from './PageState.vue'

describe('PageState', () => {
  it('keeps existing content visible while refreshing a populated list', () => {
    const root = document.createElement('div')
    const app = createApp(
      defineComponent({
        setup() {
          const loading = ref(true)

          return () =>
            h(
              PageState,
              {
                loading: loading.value,
                preserveContentOnLoading: true,
              },
              { default: () => h('table', '已有数据') },
            )
        },
      }),
    )

    app.mount(root)

    expect(root.querySelector('table')?.textContent).toBe('已有数据')
    expect(root.querySelector('[aria-busy="true"]')).not.toBeNull()
    expect(root.textContent).toContain('加载中…')

    app.unmount()
  })
})
