<script setup lang="ts">
import { nextTick, ref } from 'vue'

import { streamAssistantQuery, type AssistantStreamEvent } from '@/api/assistant'

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  resultCount?: number
}

const conversationId = crypto.randomUUID().replaceAll('-', '')
const messages = ref<Message[]>([
  {
    id: 1,
    role: 'assistant',
    content: '你好，我可以根据你的权限查询用户、合作社、仓库、产品、批次、库存、预警和预测数据。',
  },
])
const draft = ref('')
const loading = ref(false)
const error = ref('')
const turnsUsed = ref(0)
const maxTurns = ref(3)
const messageList = ref<HTMLElement | null>(null)
let nextMessageId = 2

async function scrollToLatest(): Promise<void> {
  await nextTick()
  messageList.value?.scrollTo({ top: messageList.value.scrollHeight, behavior: 'smooth' })
}

function handleEvent(event: AssistantStreamEvent, assistantMessage: Message): void {
  if (event.event === 'start') {
    maxTurns.value = event.maxTurns
  } else if (event.event === 'token') {
    assistantMessage.content += event.content
    void scrollToLatest()
  } else if (event.event === 'result') {
    assistantMessage.resultCount = event.totalItems
  } else if (event.event === 'done') {
    turnsUsed.value = event.turnsUsed
    maxTurns.value = event.maxTurns
  } else if (event.event === 'error') {
    error.value = event.message
    assistantMessage.content = event.message
  }
}

async function submit(): Promise<void> {
  const message = draft.value.trim()
  if (!message || loading.value) return
  draft.value = ''
  error.value = ''
  const userMessage: Message = { id: nextMessageId++, role: 'user', content: message }
  const assistantMessage: Message = { id: nextMessageId++, role: 'assistant', content: '' }
  messages.value.push(userMessage, assistantMessage)
  loading.value = true
  await scrollToLatest()
  try {
    await streamAssistantQuery(
      { message, conversationId },
      (event) => handleEvent(event, assistantMessage),
    )
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '智能查询失败。'
    assistantMessage.content = error.value
  } finally {
    loading.value = false
    await scrollToLatest()
  }
}

function handleKeydown(event: KeyboardEvent): void {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    void submit()
  }
}
</script>

<template>
  <section class="assistant-page">
    <header class="assistant-page__header">
      <div>
        <p class="eyebrow">QUERY ASSISTANT</p>
        <h1>智能查询</h1>
        <p class="assistant-page__intro">用大白话查询你有权限看到的业务数据，结果会实时返回。</p>
      </div>
      <span class="assistant-page__badge">已使用 {{ turnsUsed }}/{{ maxTurns }} 回合</span>
    </header>

    <div class="assistant-page__notice" role="note">
      <span aria-hidden="true">i</span>
      这是业务查询助手，不是长记忆聊天机器人；当前只保留最近 {{ maxTurns }} 回合，请尽量一次说清楚查询对象和条件。
    </div>

    <section ref="messageList" class="assistant-chat" aria-live="polite" aria-label="智能查询对话">
      <article v-for="message in messages" :key="message.id" class="assistant-message" :class="`assistant-message--${message.role}`">
        <div class="assistant-message__avatar" aria-hidden="true">{{ message.role === 'user' ? '我' : '农' }}</div>
        <div class="assistant-message__body">
          <span class="assistant-message__label">{{ message.role === 'user' ? '你' : '查询助手' }}</span>
          <p>{{ message.content || '正在查询…' }}</p>
          <small v-if="message.role === 'assistant' && message.resultCount !== undefined" class="assistant-message__result">
            已检索 {{ message.resultCount }} 条相关记录
          </small>
        </div>
      </article>
    </section>

    <form class="assistant-composer" @submit.prevent="submit">
      <textarea
        v-model="draft"
        rows="3"
        maxlength="2000"
        placeholder="例如：查询一号仓库库存低于安全库存的玉米"
        :disabled="loading"
        @keydown="handleKeydown"
      ></textarea>
      <div class="assistant-composer__footer">
        <span>Enter 发送，Shift + Enter 换行</span>
        <button type="submit" :disabled="loading || !draft.trim()">{{ loading ? '查询中…' : '发送查询' }}</button>
      </div>
    </form>
    <p v-if="error" class="assistant-page__error" role="alert">{{ error }}</p>
  </section>
</template>

<style scoped>
.assistant-page {
  display: grid;
  gap: var(--space-5);
  max-width: 70rem;
  margin: 0 auto;
}

.assistant-page__header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: var(--space-5);
}

.eyebrow {
  margin: 0 0 var(--space-2);
  color: var(--color-grain-700);
  font-size: var(--font-size-xs);
  font-weight: 800;
  letter-spacing: 0.14em;
}

h1 {
  margin: 0;
  color: var(--color-text);
  font-family: var(--font-family-display);
  font-size: clamp(2rem, 4vw, 3rem);
}

.assistant-page__intro {
  margin: var(--space-2) 0 0;
  color: var(--color-text-secondary);
}

.assistant-page__badge {
  flex: 0 0 auto;
  border: 1px solid var(--color-brand-soft);
  border-radius: var(--radius-pill);
  padding: var(--space-2) var(--space-3);
  background: var(--color-brand-50);
  color: var(--color-brand-900);
  font-size: var(--font-size-sm);
  font-weight: 700;
}

.assistant-page__notice {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  border: 1px solid var(--color-accent-soft);
  border-radius: var(--radius-md);
  padding: var(--space-3) var(--space-4);
  background: var(--color-accent-soft);
  color: var(--color-grain-700);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-relaxed);
}

.assistant-page__notice span {
  display: grid;
  width: 1.25rem;
  height: 1.25rem;
  flex: 0 0 1.25rem;
  place-items: center;
  border: 1px solid currentColor;
  border-radius: 50%;
  font-size: var(--font-size-xs);
  font-weight: 800;
}

.assistant-chat {
  display: grid;
  max-height: 52dvh;
  gap: var(--space-5);
  overflow-y: auto;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: clamp(var(--space-4), 4vw, var(--space-8));
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.assistant-message {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  max-width: 84%;
}

.assistant-message--user {
  justify-self: end;
  flex-direction: row-reverse;
}

.assistant-message__avatar {
  display: grid;
  width: 2rem;
  height: 2rem;
  flex: 0 0 2rem;
  place-items: center;
  border-radius: 0.65rem;
  background: var(--color-brand-900);
  color: var(--color-text-on-brand);
  font-size: var(--font-size-sm);
  font-weight: 800;
}

.assistant-message--user .assistant-message__avatar {
  background: var(--color-accent);
  color: var(--color-brand-950);
}

.assistant-message__body {
  min-width: 0;
}

.assistant-message__label {
  display: block;
  margin-bottom: var(--space-1);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-weight: 700;
}

.assistant-message__body p {
  margin: 0;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  border: 1px solid var(--color-border);
  border-radius: 0 var(--radius-md) var(--radius-md) var(--radius-md);
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface-muted);
  color: var(--color-text);
  line-height: var(--line-height-relaxed);
}

.assistant-message--user .assistant-message__body p {
  border-color: var(--color-brand-soft);
  border-radius: var(--radius-md) 0 var(--radius-md) var(--radius-md);
  background: var(--color-brand-50);
}

.assistant-message__result {
  display: block;
  margin-top: var(--space-2);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.assistant-composer {
  display: grid;
  gap: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  background: var(--color-surface);
  box-shadow: var(--shadow-md);
}

.assistant-composer textarea {
  width: 100%;
  resize: vertical;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--color-text);
  font: inherit;
  line-height: var(--line-height-relaxed);
}

.assistant-composer__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.assistant-composer button {
  min-height: 2.5rem;
  border: 0;
  border-radius: var(--radius-md);
  padding: 0 var(--space-4);
  background: var(--color-brand-800);
  color: var(--color-white);
  font-weight: 700;
  cursor: pointer;
}

.assistant-composer button:hover:not(:disabled) {
  background: var(--color-brand-hover);
}

.assistant-composer button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.assistant-page__error {
  margin: 0;
  color: var(--color-danger);
  font-size: var(--font-size-sm);
}

@media (max-width: 40rem) {
  .assistant-page__header {
    align-items: flex-start;
    flex-direction: column;
  }

  .assistant-message {
    max-width: 94%;
  }

  .assistant-composer__footer {
    align-items: flex-end;
    flex-direction: column;
  }
}
</style>
