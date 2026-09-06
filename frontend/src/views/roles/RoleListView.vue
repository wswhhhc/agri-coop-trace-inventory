<script setup lang="ts">
import { ref } from 'vue'

import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'

const loading = ref(false)
const error = ref('')
const empty = ref(false)

function loadData(): void {
  // 等待后端提供 /roles 和 /permissions 后接入真实请求。
  error.value = ''
  empty.value = false
}
</script>

<template>
  <section class="role-list-page">
    <PageHeader title="角色与权限" description="角色权限管理占位页面。" />
    <PageContext />
    <PageState :loading="loading" :error="error" :empty="empty" @retry="loadData">
      <p class="role-list-page__placeholder">
        当前运行中的 OpenAPI 尚未提供 /roles 和 /permissions 接口，暂不发起猜测性请求。
      </p>
    </PageState>
  </section>
</template>
