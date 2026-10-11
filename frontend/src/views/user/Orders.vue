<template>
  <div>
    <div class="page-header">
      <h3 class="page-title">我的订单</h3>
      <el-radio-group v-model="status" @change="reload">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button v-for="o in statusOptions" :key="o.value" :value="o.value">{{ o.label }}</el-radio-button>
      </el-radio-group>
    </div>

    <el-card shadow="never">
      <el-table :data="orders" v-loading="loading" stripe>
        <el-table-column prop="order_no" label="订单号" width="190" />
        <el-table-column prop="store_name" label="门店" width="180" show-overflow-tooltip />
        <el-table-column prop="item_name" label="养护项目" show-overflow-tooltip />
        <el-table-column label="到店时间" width="180">
          <template #default="{ row }">{{ row.slot_date }} {{ row.start_time }}-{{ row.end_time }}</template>
        </el-table-column>
        <el-table-column label="金额" width="100">
          <template #default="{ row }">¥{{ Number(row.total_price).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }"><StatusTag :status="row.status" /></template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="showDetail(row)">详情</el-button>
            <el-button
              v-if="row.status === 'pending' || row.status === 'confirmed'"
              link
              type="danger"
              @click="cancel(row)"
            >取消预约</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无订单，去门店预约一次养护吧" />
        </template>
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

    <el-dialog v-model="detailVisible" title="订单详情" width="560px">
      <el-descriptions v-if="current" :column="1" border>
        <el-descriptions-item label="订单号">{{ current.order_no }}</el-descriptions-item>
        <el-descriptions-item label="状态"><StatusTag :status="current.status" /></el-descriptions-item>
        <el-descriptions-item label="门店">{{ current.store_name }}</el-descriptions-item>
        <el-descriptions-item label="养护项目">{{ current.item_name }}（约 {{ current.duration }} 分钟）</el-descriptions-item>
        <el-descriptions-item label="车辆">{{ current.plate_no }}</el-descriptions-item>
        <el-descriptions-item label="到店时间">{{ current.slot_date }} {{ current.start_time }}-{{ current.end_time }}</el-descriptions-item>
        <el-descriptions-item label="金额">¥{{ Number(current.total_price).toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="联系人">{{ current.contact_name || '—' }} {{ current.contact_phone || '' }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ current.remark || '—' }}</el-descriptions-item>
        <el-descriptions-item v-if="current.reject_reason" label="拒绝原因">{{ current.reject_reason }}</el-descriptions-item>
        <el-descriptions-item v-if="current.service_note" label="服务记录">{{ current.service_note }}</el-descriptions-item>
        <el-descriptions-item label="下单时间">{{ current.created_at }}</el-descriptions-item>
      </el-descriptions>
      <el-timeline class="mt-12">
        <el-timeline-item v-for="(t, i) in timeline" :key="i" :timestamp="t.time" :type="t.type">
          {{ t.text }}
        </el-timeline-item>
      </el-timeline>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import StatusTag from '../../components/StatusTag.vue'
import { ORDER_STATUS_OPTIONS, orderStatusText } from '../../utils/format'
import { reservationApi } from '../../api'

const statusOptions = ORDER_STATUS_OPTIONS
const orders = ref([])
const loading = ref(false)
const status = ref('')
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

const detailVisible = ref(false)
const current = ref(null)

const timeline = computed(() => {
  const c = current.value
  if (!c) return []
  const list = [{ text: `提交预约（${orderStatusText('pending')}）`, time: c.created_at, type: 'primary' }]
  if (c.confirmed_at) list.push({ text: '门店确认受理', time: c.confirmed_at, type: 'success' })
  if (c.status === 'in_service') list.push({ text: '服务进行中', time: '', type: 'info' })
  if (c.completed_at) list.push({ text: '服务已完成', time: c.completed_at, type: 'success' })
  if (c.cancelled_at) list.push({ text: '订单已取消', time: c.cancelled_at, type: 'info' })
  if (c.status === 'rejected') list.push({ text: `门店拒绝：${c.reject_reason || ''}`, time: '', type: 'danger' })
  return list
})

async function load() {
  loading.value = true
  try {
    const data = await reservationApi.list({ page: page.value, page_size: pageSize.value, status: status.value || undefined })
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

function cancel(row) {
  ElMessageBox.confirm(`确定取消订单 ${row.order_no} 吗？取消后该时段将释放。`, '取消预约', { type: 'warning' })
    .then(async () => {
      await reservationApi.cancel(row.id)
      ElMessage.success('订单已取消')
      load()
    })
    .catch(() => {})
}

onMounted(load)
</script>
