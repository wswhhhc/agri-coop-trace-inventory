<script setup lang="ts">
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
</script>

<template>
  <section class="not-found-page">
    <PageHeader title="404 页面不存在" description="请求的后台页面不存在。" />
    <PageContext />
    <p class="not-found-page__placeholder">请检查地址，或从左侧菜单重新进入功能页面。</p>
  </section>
</template>
