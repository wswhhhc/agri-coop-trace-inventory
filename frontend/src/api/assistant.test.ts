import { afterEach, describe, expect, it, vi } from 'vitest'

import { streamAssistantQuery } from './assistant'

afterEach(() => {
  vi.restoreAllMocks()
})

describe('assistant api', () => {
  it('parses SSE start, streamed tokens, result and completion events', async () => {
    const body = new ReadableStream<Uint8Array>({
      start(controller) {
        const encoder = new TextEncoder()
        controller.enqueue(
          encoder.encode(
            'event: start\ndata: {"conversationId":"c1","maxTurns":3}\n\n' +
              'event: token\ndata: {"content":"查询"}\n\n',
          ),
        )
        controller.enqueue(
          encoder.encode(
            'event: result\ndata: {"resource":"inventories","totalItems":2}\n\n' +
              'event: done\ndata: {"conversationId":"c1","turnsUsed":1,"maxTurns":3}\n\n',
          ),
        )
        controller.close()
      },
    })
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, body }))
    const events: string[] = []

    await streamAssistantQuery(
      { message: '查询库存', conversationId: 'c1' },
      (event) => events.push(event.event),
    )

    expect(events).toEqual(['start', 'token', 'result', 'done'])
  })

  it('reports an HTTP failure before opening the stream', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 401 }))

    await expect(
      streamAssistantQuery(
        { message: '查询用户', conversationId: 'c1' },
        () => undefined,
      ),
    ).rejects.toThrow('登录状态已失效')
  })

  it('waits for asynchronous event handlers before processing the next event', async () => {
    const body = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(
          new TextEncoder().encode(
            'event: start\ndata: {"conversationId":"c1","maxTurns":3}\n\n' +
              'event: token\ndata: {"content":"查询"}\n\n',
          ),
        )
        controller.close()
      },
    })
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, body }))
    const events: string[] = []
    let releaseStart!: () => void
    const startReleased = new Promise<void>((resolve) => {
      releaseStart = resolve
    })

    const streamPromise = streamAssistantQuery(
      { message: '查询库存', conversationId: 'c1' },
      async (event) => {
        events.push(event.event)
        if (event.event === 'start') await startReleased
      },
    )

    await new Promise((resolve) => setTimeout(resolve, 0))
    expect(events).toEqual(['start'])
    releaseStart()
    await streamPromise
    expect(events).toEqual(['start', 'token'])
  })
})
