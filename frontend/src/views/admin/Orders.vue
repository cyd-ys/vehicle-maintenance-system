<template>
  <div>
    <div class="page-header">
      <h3 class="page-title">预约订单查询（全平台）</h3>
      <div style="display: flex; gap: 10px">
        <el-input v-model="keyword" placeholder="搜索订单号/项目" style="width: 220px" clearable @keyup.enter="reload" @clear="reload" />
        <el-select v-model="status" placeholder="全部状态" style="width: 140px" clearable @change="reload">
          <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
      </div>
    </div>

    <el-card shadow="never">
      <el-table :data="orders" v-loading="loading" stripe>
        <el-table-column prop="order_no" label="订单号" width="190" />
        <el-table-column prop="store_name" label="门店" width="170" show-overflow-tooltip />
        <el-table-column prop="customer_name" label="客户" width="100" />
        <el-table-column prop="item_name" label="项目" show-overflow-tooltip />
        <el-table-column label="到店时间" width="180">
          <template #default="{ row }">{{ row.slot_date }} {{ row.start_time }}-{{ row.end_time }}</template>
        </el-table-column>
        <el-table-column label="金额" width="100">
          <template #default="{ row }">¥{{ Number(row.total_price).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }"><StatusTag :status="row.status" /></template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="showDetail(row)">详情</el-button>
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

    <el-dialog v-model="detailVisible" title="订单详情" width="540px">
      <el-descriptions v-if="current" :column="1" border>
        <el-descriptions-item label="订单号">{{ current.order_no }}</el-descriptions-item>
        <el-descriptions-item label="状态"><StatusTag :status="current.status" /></el-descriptions-item>
        <el-descriptions-item label="门店">{{ current.store_name }}</el-descriptions-item>
        <el-descriptions-item label="客户">{{ current.customer_name }}（{{ current.contact_phone || '—' }}）</el-descriptions-item>
        <el-descriptions-item label="项目">{{ current.item_name }}</el-descriptions-item>
        <el-descriptions-item label="车辆">{{ current.plate_no }}</el-descriptions-item>
        <el-descriptions-item label="到店时间">{{ current.slot_date }} {{ current.start_time }}-{{ current.end_time }}</el-descriptions-item>
        <el-descriptions-item label="金额">¥{{ Number(current.total_price).toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="下单时间">{{ current.created_at }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import StatusTag from '../../components/StatusTag.vue'
import { ORDER_STATUS_OPTIONS } from '../../utils/format'
import { adminApi } from '../../api'

const statusOptions = ORDER_STATUS_OPTIONS
const orders = ref([])
const loading = ref(false)
const status = ref('')
const keyword = ref('')
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

const detailVisible = ref(false)
const current = ref(null)

async function load() {
  loading.value = true
  try {
    const data = await adminApi.orders({
      page: page.value,
      page_size: pageSize.value,
      status: status.value || undefined,
      keyword: keyword.value || undefined
    })
    orders.value = data.items
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

function showDetail(row) {
  current.value = row
  detailVisible.value = true
}

onMounted(load)
</script>
