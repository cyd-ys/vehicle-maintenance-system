<template>
  <div>
    <div class="page-header">
      <h3 class="page-title">操作日志</h3>
      <el-input v-model="action" placeholder="按操作类型筛选，如 登录/提交预约" style="width: 260px" clearable @keyup.enter="reload" @clear="reload" />
    </div>

    <el-card shadow="never">
      <el-table :data="logs" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="operator_name" label="操作人" width="140" />
        <el-table-column label="角色" width="130">
          <template #default="{ row }">{{ USER_ROLE[row.role] || row.role || '—' }}</template>
        </el-table-column>
        <el-table-column prop="action" label="操作" width="140" />
        <el-table-column label="对象" width="150">
          <template #default="{ row }">
            <span v-if="row.target_type">{{ row.target_type }}#{{ row.target_id }}</span>
            <span v-else>—</span>
          </template>
        </el-table-column>
        <el-table-column prop="detail" label="详情" show-overflow-tooltip />
        <el-table-column prop="created_at" label="时间" width="180" />
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
import { adminApi } from '../../api'
import { USER_ROLE } from '../../utils/format'

const logs = ref([])
const loading = ref(false)
const action = ref('')
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

async function load() {
  loading.value = true
  try {
    const data = await adminApi.logs({
      page: page.value,
      page_size: pageSize.value,
      action: action.value || undefined
    })
    logs.value = data.items
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

onMounted(load)
</script>
