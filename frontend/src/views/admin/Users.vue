<template>
  <div>
    <div class="page-header">
      <h3 class="page-title">用户管理</h3>
      <div style="display: flex; gap: 10px">
        <el-input v-model="keyword" placeholder="搜索用户名/姓名" style="width: 220px" clearable @keyup.enter="reload" @clear="reload" />
        <el-select v-model="role" placeholder="全部角色" style="width: 150px" clearable @change="reload">
          <el-option label="普通用户" value="user" />
          <el-option label="门店工作人员" value="store" />
          <el-option label="系统管理员" value="admin" />
        </el-select>
      </div>
    </div>

    <el-card shadow="never">
      <el-table :data="users" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="用户名" width="140" />
        <el-table-column prop="real_name" label="姓名" width="120" />
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column label="角色" width="140">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : row.role === 'store' ? 'success' : ''" size="small">
              {{ USER_ROLE[row.role] || row.role }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">{{ row.status === 1 ? '正常' : '已停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" width="180" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.role !== 'admin'"
              link
              :type="row.status === 1 ? 'danger' : 'success'"
              @click="toggle(row)"
            >{{ row.status === 1 ? '停用' : '启用' }}</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-if="total > pageSize"
        class="mt-12"
        layout="prev, pager, next, total"
        :total="total"
        :page-size="pageSize"
        :current-page="page"
        @current-change="onPage"
      />
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminApi } from '../../api'
import { USER_ROLE } from '../../utils/format'

const users = ref([])
const loading = ref(false)
const role = ref('')
const keyword = ref('')
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

async function load() {
  loading.value = true
  try {
    const data = await adminApi.users({
      page: page.value,
      page_size: pageSize.value,
      role: role.value || undefined,
      keyword: keyword.value || undefined
    })
    users.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function reload() {
  page.value = 1
  load()
}

function onPage(p) {
  page.value = p
  load()
}

function toggle(row) {
  const target = row.status === 1 ? 0 : 1
  const word = target === 0 ? '停用' : '启用'
  ElMessageBox.confirm(`确定${word}账号「${row.username}」吗？`, '提示', { type: 'warning' })
    .then(async () => {
      await adminApi.userStatus(row.id, target)
      ElMessage.success(`账号已${word}`)
      load()
    })
    .catch(() => {})
}

onMounted(load)
</script>
