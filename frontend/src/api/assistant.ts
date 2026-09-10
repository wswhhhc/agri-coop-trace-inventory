import { getAccessToken } from './session'

export interface AssistantQueryPayload {
  message: string
  conversationId: string
}

export type AssistantStreamEvent =
  | { event: 'start'; conversationId: string; maxTurns: number }
  | { event: 'token'; content: string }
  | { event: 'result'; resource: string; totalItems: number }
  | { event: 'done'; conversationId: string; turnsUsed: number; maxTurns: number }
  | { event: 'error'; code: string; message: string }

type EventHandler = (event: AssistantStreamEvent) => void | Promise<void>

function parseEvent(block: string): AssistantStreamEvent | null {
  const lines = block.split(/\r?\n/)
  const event = lines.find((line) => line.startsWith('event:'))?.slice(6).trim()
  const data = lines
    .filter((line) => line.startsWith('data:'))
    .map((line) => line.slice(5).trimStart())
    .join('\n')
  if (!event || !data) return null

  const payload = JSON.parse(data) as Record<string, unknown>
  if (event === 'start') {
    return {
      event,
      conversationId: String(payload.conversationId),
      maxTurns: Number(payload.maxTurns),
    }
  }
  if (event === 'token') return { event, content: String(payload.content ?? '') }
  if (event === 'result') {
    return {
      event,
      resource: String(payload.resource ?? ''),
      totalItems: Number(payload.totalItems ?? 0),
    }
  }
  if (event === 'done') {
    return {
      event,
      conversationId: String(payload.conversationId),
      turnsUsed: Number(payload.turnsUsed),
      maxTurns: Number(payload.maxTurns),
    }
  }
  if (event === 'error') {
    return {
      event,
      code: String(payload.code ?? 'ASSISTANT_QUERY_FAILED'),
      message: String(payload.message ?? '智能查询失败'),
    }
  }
  return null
}

export async function streamAssistantQuery(
  payload: AssistantQueryPayload,
  onEvent: EventHandler,
  signal?: AbortSignal,
): Promise<void> {
  const token = getAccessToken()
  const response = await fetch(`${import.meta.env.VITE_API_BASE_URL ?? '/api/v1'}/assistant/query`, {
    method: 'POST',
    headers: {
      Accept: 'text/event-stream',
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    credentials: 'include',
    body: JSON.stringify(payload),
    signal,
  })

  if (!response.ok) {
    throw new Error(response.status === 401 ? '登录状态已失效，请重新登录。' : '智能查询请求失败。')
  }
  if (!response.body) throw new Error('浏览器不支持流式响应。')

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    buffer += decoder.decode(value, { stream: !done })
    const blocks = buffer.split(/\r?\n\r?\n/)
    buffer = blocks.pop() ?? ''
    for (const block of blocks) {
      const event = parseEvent(block)
      if (event) await onEvent(event)
    }
    if (done) break
  }
  const finalEvent = parseEvent(buffer)
  if (finalEvent) await onEvent(finalEvent)
}
