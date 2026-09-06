<script setup lang="ts">
import { computed, ref } from 'vue'

import { listPermissions, listRoles, updateRolePermissions } from '@/api/roles'
import PageContext from '@/components/common/PageContext.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageState from '@/components/common/PageState.vue'
import { usePageData } from '@/composables/usePageData'
import { useAuthStore } from '@/stores/auth'
import { getApiErrorMessage } from '@/utils/api-error'

const authStore = useAuthStore()
const canManage = computed(() => authStore.role === 'SYSTEM_ADMIN')
const roleState = usePageData(listRoles, [])
const permissionState = usePageData(listPermissions, [])
const editingRoleId = ref<string | null>(null)
const selectedPermissionCodes = ref<string[]>([])
const submitting = ref(false)
const formError = ref('')
const successMessage = ref('')

function beginEdit(role: (typeof roleState.data.value)[number]): void {
  editingRoleId.value = role.id
  selectedPermissionCodes.value = role.permissions.map((permission) => permission.code)
  formError.value = ''
  successMessage.value = ''
}

function cancelEdit(): void {
  editingRoleId.value = null
  formError.value = ''
}

async function handleUpdate(): Promise<void> {
  if (!editingRoleId.value) return
  submitting.value = true
  formError.value = ''
  successMessage.value = ''
  try {
    await updateRolePermissions(editingRoleId.value, selectedPermissionCodes.value)
    cancelEdit()
    successMessage.value = '角色权限更新成功。'
    await roleState.loadData()
  } catch (reason) {
    formError.value = getApiErrorMessage(reason)
  } finally {
    submitting.value = false
  }
}

async function loadData(): Promise<void> {
  await Promise.all([roleState.loadData(), permissionState.loadData()])
}
</script>

<template>
  <section class="role-list-page">
    <PageHeader eyebrow="权限治理" title="角色与权限" description="查看角色权限并维护系统角色授权。" />
    <PageContext />
    <PageState
      :loading="roleState.loading || permissionState.loading"
      :error="roleState.error || permissionState.error"
      :empty="roleState.data.length === 0"
      empty-message="暂无角色数据"
      @retry="loadData"
    >
      <p v-if="!canManage" role="alert">只有系统管理员可以维护角色权限。</p>
      <p v-if="formError" role="alert">{{ formError }}</p>
      <p v-if="successMessage" role="status">{{ successMessage }}</p>
      <table>
        <caption>角色列表</caption>
        <thead>
          <tr>
            <th scope="col">编码</th>
            <th scope="col">名称</th>
            <th scope="col">说明</th>
            <th scope="col">权限</th>
            <th v-if="canManage" scope="col">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="role in roleState.data" :key="role.id">
            <td>{{ role.code }}</td>
            <td>{{ role.name }}</td>
            <td>{{ role.description || '—' }}</td>
            <td>{{ role.permissions.map((permission) => permission.code).join('、') || '无' }}</td>
            <td v-if="canManage">
              <button type="button" @click="beginEdit(role)">编辑权限</button>
            </td>
          </tr>
        </tbody>
      </table>
    </PageState>

    <form v-if="canManage && editingRoleId" class="role-permission-edit-form" @submit.prevent="handleUpdate">
      <h2>编辑角色权限</h2>
      <label v-for="permission in permissionState.data" :key="permission.id">
        <input v-model="selectedPermissionCodes" type="checkbox" :value="permission.code" />
        {{ permission.name }}（{{ permission.code }}）
      </label>
      <button type="submit" :disabled="submitting">{{ submitting ? '保存中…' : '保存' }}</button>
      <button type="button" :disabled="submitting" @click="cancelEdit">取消</button>
    </form>
  </section>
</template>
