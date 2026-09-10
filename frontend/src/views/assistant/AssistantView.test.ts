import { createApp, nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const { streamAssistantQueryMock } = vi.hoisted(() => ({
  streamAssistantQueryMock: vi.fn(),
}))

vi.mock('@/api/assistant', () => ({
  streamAssistantQuery: streamAssistantQueryMock,
}))

import AssistantView from './AssistantView.vue'

async function flushPromises(): Promise<void> {
  await Promise.resolve()
  await nextTick()
  await new Promise((resolve) => setTimeout(resolve, 0))
  await nextTick()
}

function latestAssistantText(root: HTMLElement): string {
  const messages = root.querySelectorAll('.assistant-message--assistant p')
  return messages[messages.length - 1]?.textContent ?? ''
}

describe('AssistantView', () => {
  beforeEach(() => {
    vi.stubGlobal('crypto', { randomUUID: () => 'conversation-id' })
    vi.stubGlobal('requestAnimationFrame', (callback: FrameRequestCallback) => {
      return window.setTimeout(() => callback(performance.now()), 0)
    })
    streamAssistantQueryMock.mockReset()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    document.body.innerHTML = ''
  })

  it('renders each streamed token before the response completes', async () => {
    let releaseSecondToken!: () => void
    const secondTokenReleased = new Promise<void>((resolve) => {
      releaseSecondToken = resolve
    })
    streamAssistantQueryMock.mockImplementation(async (_payload, onEvent) => {
      await onEvent({ event: 'start', conversationId: 'conversation-id', maxTurns: 3 })
      await onEvent({ event: 'token', content: '第一段' })
      await secondTokenReleased
      await onEvent({ event: 'token', content: '第二段' })
      await onEvent({
        event: 'done',
        conversationId: 'conversation-id',
        turnsUsed: 1,
        maxTurns: 3,
      })
    })

    const root = document.createElement('div')
    document.body.append(root)
    const app = createApp(AssistantView)
    app.mount(root)
    Object.defineProperty(root.querySelector('.assistant-chat'), 'scrollTo', {
      configurable: true,
      value: vi.fn(),
    })

    const textarea = root.querySelector('textarea') as HTMLTextAreaElement
    textarea.value = '查询库存'
    textarea.dispatchEvent(new Event('input', { bubbles: true }))
    await nextTick()
    ;(root.querySelector('button[type="submit"]') as HTMLButtonElement).click()

    await flushPromises()
    expect(latestAssistantText(root)).toBe('第一段')

    releaseSecondToken()
    await flushPromises()
    expect(latestAssistantText(root)).toBe('第一段第二段')

    app.unmount()
  })
})
