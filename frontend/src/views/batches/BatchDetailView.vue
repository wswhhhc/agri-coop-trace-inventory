<script setup lang="ts">
import { computed, reactive, ref, toRefs, watch } from 'vue'
import { useRoute } from 'vue-router'

import { getBatch, updateBatch, type BatchStatus } from '@/api/batches'
import { getPublicQrCodeUrl } from '@/api/public-traceability'
import QualityInspectionPanel from '@/components/batches/QualityInspectionPanel.vue'
import TraceEventTimeline from '@/components/batches/TraceEventTimeline.vue'
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { usePageData } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import { getApiErrorMessage } from '@/utils/api-error'

const route = useRoute()
const batchId = String(route.params.batchId)
const pageState = usePageData(() => getBatch(batchId), null)
const { data, loading, error } = toRefs(pageState)
const { loadData } = pageState
const authStore = useAuthStore()
const canManage = computed(() => authStore.hasPermission('batch:manage'))
const updating = ref(false)
const updateError = ref('')
const successMessage = ref('')
const statusOptions: BatchStatus[] = ['CREATED', 'IN_STOCK', 'DEPLETED', 'BLOCKED', 'EXPIRED']
const statusLabels: Record<BatchStatus, string> = {
  CREATED: '已创建',
  IN_STOCK: '库存中',
  DEPLETED: '已耗尽',
  BLOCKED: '已冻结',
  EXPIRED: '已过期',
}
const form = reactive({
  origin: '',
  expiryDate: '',
  responsiblePerson: '',
  status: 'CREATED' as BatchStatus,
})

function batchStatusTone(value: string): 'success' | 'warning' | 'danger' | 'info' {
  if (value === 'IN_STOCK') return 'success'
  if (value === 'EXPIRED' || value === 'BLOCKED') return 'danger'
  if (value === 'DEPLETED') return 'warning'
  return 'info'
}

function batchStatusLabel(value: string): string {
  return statusLabels[value as BatchStatus] ?? value
}

watch(data, syncForm)

function syncForm(): void {
  if (!data.value) return
  form.origin = data.value.origin
  form.expiryDate = data.value.expiryDate
  form.responsiblePerson = data.value.responsiblePerson ?? ''
  form.status = data.value.status as BatchStatus
}

async function handleUpdate(): Promise<void> {
  if (!data.value) return
  updating.value = true
  updateError.value = ''
  successMessage.value = ''
  try {
    await updateBatch(batchId, {
      origin: form.origin.trim(),
      expiryDate: form.expiryDate,
      responsiblePerson: form.responsiblePerson.trim() || null,
      status: form.status,
    })
    await loadData()
    syncForm()
    successMessage.value = '批次更新成功。'
  } catch (reason) {
    updateError.value = getApiErrorMessage(reason)
  } finally {
    updating.value = false
  }
}
</script>

<template>
  <section class="batch-detail-page">
    <PageHeader eyebrow="批次档案" title="批次详情" description="查看批次基础信息和服务端生成的追溯码。" />
    <PageContext />
    <PageState
      :loading="loading"
      :error="error"
      :empty="!data"
      empty-message="未找到批次"
      @retry="loadData"
    >
      <div class="batch-detail-content">
        <section class="batch-hero" aria-labelledby="batch-hero-title">
          <div class="batch-hero__intro">
            <div class="batch-hero__stamp" aria-hidden="true">批</div>
            <div>
              <p class="batch-hero__kicker">TRACEABLE PRODUCE / 批次档案</p>
              <h2 id="batch-hero-title">{{ data?.batchNo }}</h2>
              <p>从产地到库存，每一条流转信息都在这里留档。</p>
            </div>
          </div>
          <div v-if="data" class="batch-hero__status">
            <span>当前状态</span>
            <StatusBadge :label="batchStatusLabel(data.status)" :tone="batchStatusTone(data.status)" />
          </div>
        </section>

        <div class="batch-overview-grid">
          <section class="batch-card batch-info-card" aria-labelledby="batch-info-title">
            <div class="batch-card__heading">
              <div>
                <p class="batch-card__eyebrow">01 / ARCHIVE</p>
                <h2 id="batch-info-title">基础信息</h2>
              </div>
              <span class="batch-card__mark" aria-hidden="true">01</span>
            </div>
            <dl class="batch-info-grid">
              <div class="batch-info-grid__item batch-info-grid__item--wide">
                <dt>批次编号</dt>
                <dd>{{ data?.batchNo }}</dd>
              </div>
              <div class="batch-info-grid__item batch-info-grid__item--wide">
                <dt>追溯码</dt>
                <dd class="batch-code">{{ data?.traceCode }}</dd>
              </div>
              <div class="batch-info-grid__item">
                <dt>产品 ID</dt>
                <dd class="batch-code">{{ data?.productId }}</dd>
              </div>
              <div class="batch-info-grid__item">
                <dt>负责人</dt>
                <dd>{{ data?.responsiblePerson || '—' }}</dd>
              </div>
              <div class="batch-info-grid__item">
                <dt>产地</dt>
                <dd>{{ data?.origin }}</dd>
              </div>
              <div class="batch-info-grid__item">
                <dt>生产日期</dt>
                <dd>{{ data?.productionDate }}</dd>
              </div>
              <div class="batch-info-grid__item">
                <dt>到期日期</dt>
                <dd>{{ data?.expiryDate }}</dd>
              </div>
            </dl>
          </section>

          <section class="batch-card batch-qr-card" aria-labelledby="batch-qr-title">
            <div class="batch-card__heading">
              <div>
                <p class="batch-card__eyebrow">02 / PUBLIC TRACE</p>
                <h2 id="batch-qr-title">扫码查批次</h2>
              </div>
              <span class="batch-card__mark batch-card__mark--accent" aria-hidden="true">QR</span>
            </div>
            <div class="batch-qr-card__body">
              <div class="batch-qr-card__image-wrap">
                <img
                  :src="getPublicQrCodeUrl(data.traceCode)"
                  :alt="`批次 ${data.batchNo} 的公开追溯二维码`"
                  loading="lazy"
                  decoding="async"
                  width="180"
                  height="180"
                />
              </div>
              <div class="batch-qr-card__copy">
                <p>将二维码交给消费者，即可公开查看该批次的产地、日期和追溯记录。</p>
                <RouterLink class="batch-qr-card__link" :to="{ name: 'public-trace', params: { traceCode: data.traceCode } }">
                  打开公开追溯页 <span aria-hidden="true">↗</span>
                </RouterLink>
              </div>
            </div>
          </section>
        </div>

        <form v-if="canManage && data" class="batch-card batch-edit-form" @submit.prevent="handleUpdate">
          <div class="batch-card__heading">
            <div>
              <p class="batch-card__eyebrow">03 / CONTROL</p>
              <h2>编辑批次</h2>
            </div>
            <span class="batch-card__hint">仅管理员可修改</span>
          </div>
          <div class="batch-edit-form__fields">
            <label>
              产地
              <input v-model="form.origin" name="origin" required maxlength="255" />
            </label>
            <label>
              到期日期
              <input v-model="form.expiryDate" type="date" name="expiryDate" required />
            </label>
            <label>
              负责人
              <input v-model="form.responsiblePerson" name="responsiblePerson" maxlength="50" />
            </label>
            <label>
              状态
              <select v-model="form.status" name="status" required>
                <option v-for="status in statusOptions" :key="status" :value="status">{{ statusLabels[status] }}</option>
              </select>
            </label>
          </div>
          <div class="batch-edit-form__footer">
            <p v-if="updateError" class="batch-form-message batch-form-message--error" role="alert">{{ updateError }}</p>
            <p v-if="successMessage" class="batch-form-message batch-form-message--success" role="status">{{ successMessage }}</p>
            <button type="submit" :disabled="updating">{{ updating ? '保存中…' : '保存修改' }}</button>
          </div>
        </form>
      </div>
    </PageState>
    <div v-if="data" class="batch-lower-grid">
      <QualityInspectionPanel class="batch-module" :batch-id="batchId" :can-manage="canManage" />
      <TraceEventTimeline class="batch-module" :batch-id="batchId" />
    </div>
  </section>
</template>

<style scoped>
.batch-detail-page {
  display: grid;
  gap: var(--space-5);
}

.batch-detail-page > .page-state {
  min-height: 0;
  border: 0;
  padding: 0;
  background: transparent;
  text-align: left;
}

.batch-detail-content {
  display: grid;
  gap: var(--space-5);
}

.batch-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-6);
  overflow: hidden;
  border: 1px solid var(--color-brand-900);
  border-radius: var(--radius-lg);
  padding: var(--space-6) var(--space-8);
  background:
    radial-gradient(circle at 90% 20%, rgb(201 154 61 / 22%), transparent 22%),
    linear-gradient(115deg, var(--color-brand-950), var(--color-brand-900));
  color: var(--color-white);
  box-shadow: var(--shadow-md);
}

.batch-hero__intro {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  min-width: 0;
}

.batch-hero__stamp {
  display: grid;
  width: 3.5rem;
  height: 3.5rem;
  flex: 0 0 auto;
  place-items: center;
  border: 1px solid rgb(255 255 255 / 28%);
  border-radius: var(--radius-md);
  background: rgb(255 255 255 / 12%);
  color: var(--color-grain-100);
  font-size: var(--font-size-xl);
  font-weight: 800;
}

.batch-hero__kicker,
.batch-card__eyebrow {
  margin-bottom: var(--space-2);
  color: var(--color-grain-500);
  font-size: var(--font-size-xs);
  font-weight: 800;
  letter-spacing: 0.1em;
}

.batch-hero__kicker {
  color: var(--color-grain-100);
  opacity: 0.78;
}

.batch-hero h2 {
  margin-bottom: var(--space-2);
  color: var(--color-white);
  font-size: clamp(1.35rem, 3vw, 2rem);
  letter-spacing: 0.02em;
}

.batch-hero p:last-child {
  margin-bottom: 0;
  color: rgb(255 255 255 / 74%);
  font-size: var(--font-size-sm);
}

.batch-hero__status {
  display: grid;
  flex: 0 0 auto;
  justify-items: end;
  gap: var(--space-2);
  color: rgb(255 255 255 / 68%);
  font-size: var(--font-size-xs);
}

.batch-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.batch-overview-grid,
.batch-lower-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) minmax(20rem, 0.85fr);
  gap: var(--space-5);
  align-items: stretch;
}

.batch-card__heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-5) var(--space-6) var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.batch-card__heading h2 {
  margin-bottom: 0;
  font-size: var(--font-size-lg);
}

.batch-card__eyebrow {
  margin-bottom: var(--space-1);
}

.batch-card__mark {
  display: grid;
  min-width: 2.5rem;
  height: 2.5rem;
  place-items: center;
  border: 1px solid var(--color-brand-soft);
  border-radius: var(--radius-md);
  background: var(--color-surface-muted);
  color: var(--color-brand);
  font-size: var(--font-size-xs);
  font-weight: 800;
  letter-spacing: 0.04em;
}

.batch-card__mark--accent {
  border-color: var(--color-accent-soft);
  background: var(--color-accent-soft);
  color: var(--color-grain-700);
}

.batch-info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1px;
  margin: 0;
  overflow: hidden;
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
  background: var(--color-border);
}

.batch-info-grid__item {
  display: grid;
  gap: var(--space-1);
  min-width: 0;
  padding: var(--space-4) var(--space-5);
  background: var(--color-surface);
}

.batch-info-grid__item--wide {
  grid-column: 1 / -1;
  grid-template-columns: 7rem minmax(0, 1fr);
  align-items: baseline;
}

.batch-info-grid dt {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.batch-info-grid dd {
  min-width: 0;
  margin: 0;
  color: var(--color-text);
  font-weight: 600;
  overflow-wrap: anywhere;
}

.batch-code {
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: var(--font-size-sm);
  letter-spacing: 0.01em;
}

.batch-qr-card {
  display: grid;
  grid-template-rows: auto 1fr;
}

.batch-qr-card__body {
  display: grid;
  grid-template-columns: minmax(10rem, 12rem) minmax(0, 1fr);
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-5) var(--space-6);
}

.batch-qr-card__image-wrap {
  display: grid;
  place-items: center;
  aspect-ratio: 1;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-3);
  background: var(--color-surface-muted);
}

.batch-qr-card__image-wrap img {
  display: block;
  width: 100%;
  height: auto;
  max-width: 10rem;
  border-radius: var(--radius-sm);
  background: var(--color-white);
}

.batch-qr-card__copy {
  display: grid;
  align-content: center;
  gap: var(--space-4);
}

.batch-qr-card__copy p {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.batch-qr-card__link {
  width: fit-content;
  font-weight: 700;
  text-decoration: none;
}

.batch-edit-form {
  overflow: hidden;
}

.batch-edit-form__fields {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-4);
  padding: var(--space-5) var(--space-6);
}

.batch-edit-form__fields label {
  display: grid;
  gap: var(--space-1);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.batch-card__hint {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.batch-edit-form__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  border-top: 1px solid var(--color-border);
  padding: var(--space-4) var(--space-6);
  background: var(--color-surface-muted);
}

.batch-form-message {
  margin: 0;
  font-size: var(--font-size-sm);
}

.batch-form-message--error {
  color: var(--color-danger);
}

.batch-form-message--success {
  color: var(--color-success);
}

.batch-lower-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.batch-module {
  min-width: 0;
}

@media (max-width: 48rem) {
  .batch-hero {
    align-items: flex-start;
    flex-direction: column;
    padding: var(--space-5);
  }

  .batch-hero__status {
    justify-items: start;
  }

  .batch-overview-grid,
  .batch-lower-grid {
    grid-template-columns: 1fr;
  }

  .batch-qr-card__body {
    grid-template-columns: minmax(9rem, 11rem) minmax(0, 1fr);
  }

  .batch-edit-form__fields {
    grid-template-columns: 1fr;
  }

  .batch-edit-form__footer {
    align-items: stretch;
    flex-direction: column;
  }

  .batch-edit-form__footer button {
    width: 100%;
  }
}

@media (max-width: 30rem) {
  .batch-card__heading,
  .batch-qr-card__body,
  .batch-edit-form__fields,
  .batch-edit-form__footer {
    padding-inline: var(--space-4);
  }

  .batch-info-grid {
    grid-template-columns: 1fr;
  }

  .batch-info-grid__item--wide {
    grid-template-columns: 1fr;
    gap: var(--space-2);
  }

  .batch-qr-card__body {
    grid-template-columns: 1fr;
  }

  .batch-qr-card__image-wrap {
    width: min(100%, 13rem);
    justify-self: center;
  }
}
</style>
