<template>
  <div>
    <div class="page-header">
      <h3 class="page-title">养护项目管理</h3>
      <div style="display: flex; gap: 10px">
        <el-select v-model="storeId" placeholder="全部门店" style="width: 200px" clearable filterable @change="reload">
          <el-option v-for="s in storeOptions" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
        <el-select v-model="status" placeholder="全部状态" style="width: 140px" clearable @change="reload">
          <el-option label="启用" :value="1" />
          <el-option label="停用" :value="0" />
        </el-select>
      </div>
    </div>

    <el-card shadow="never">
      <el-table :data="items" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="所属门店" width="180">
          <template #default="{ row }">{{ storeName(row.store_id) }}</template>
        </el-table-column>
        <el-table-column prop="name" label="项目名称" min-width="150" />
        <el-table-column prop="category" label="类别" width="110" />
        <el-table-column label="时长" width="90">
          <template #default="{ row }">{{ row.duration }} 分钟</template>
        </el-table-column>
        <el-table-column label="价格" width="110">
          <template #default="{ row }">¥{{ Number(row.price).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">{{ row.status === 1 ? '启用' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button link :type="row.status === 1 ? 'danger' : 'success'" @click="toggle(row)">
              {{ row.status === 1 ? '停用' : '启用' }}
            </el-button>
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

const items = ref([])
const loading = ref(false)
const storeId = ref('')
const status = ref('')
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const storeOptions = ref([])

function storeName(id) {
  return storeOptions.value.find((s) => s.id === id)?.name || `门店#${id}`
}

async function loadStores() {
  const data = await adminApi.stores({ page: 1, page_size: 100 })
  storeOptions.value = data.items
}

async function load() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (storeId.value) params.store_id = storeId.value
    if (status.value !== '' && status.value !== undefined && status.value !== null) params.status = status.value
    const data = await adminApi.items(params)
    items.value = data.items
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
  const word = target === 1 ? '启用' : '停用'
  ElMessageBox.confirm(`确定${word}项目「${row.name}」吗？`, '提示', { type: 'warning' })
    .then(async () => {
      await adminApi.itemStatus(row.id, target)
      ElMessage.success(`项目已${word}`)
      load()
    })
    .catch(() => {})
}

onMounted(async () => {
  await loadStores()
  load()
})
</script>
