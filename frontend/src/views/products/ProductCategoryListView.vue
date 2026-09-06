<script setup lang="ts">
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import { listProductCategories } from '@/api/product-categories'
import { useListPage } from '@/composables/usePageData'

const { items, loading, error, loadData } = useListPage(listProductCategories)
</script>

<template>
  <section class="product-category-list-page">
    <PageHeader title="产品分类" description="查看当前合作社的产品分类。" />
    <PageContext />
    <PageState :loading="loading" :error="error" :empty="items.length === 0" @retry="loadData">
      <table>
        <caption>产品分类列表</caption>
        <thead>
          <tr>
            <th scope="col">编码</th>
            <th scope="col">名称</th>
            <th scope="col">描述</th>
            <th scope="col">状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="category in items" :key="category.id">
            <td>{{ category.code }}</td>
            <td>{{ category.name }}</td>
            <td>{{ category.description || '—' }}</td>
            <td>{{ category.isActive ? '启用' : '停用' }}</td>
          </tr>
        </tbody>
      </table>
    </PageState>
  </section>
</template>
