<template>
  <div>
    <div class="page-header">
      <h3 class="page-title">预约订单处理</h3>
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
        <el-table-column prop="customer_name" label="客户" width="100" />
        <el-table-column prop="item_name" label="养护项目" show-overflow-tooltip />
        <el-table-column label="车辆" width="120">
          <template #default="{ row }">{{ row.plate_no }}</template>
        </el-table-column>
        <el-table-column label="到店时间" width="180">
          <template #default="{ row }">{{ row.slot_date }} {{ row.start_time }}-{{ row.end_time }}</template>
        </el-table-column>
        <el-table-column label="金额" width="100">
          <template #default="{ row }">¥{{ Number(row.total_price).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }"><StatusTag :status="row.status" /></template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              v-for="a in actions(row)"
              :key="a.status"
              link
              :type="a.type"
              @click="act(row, a)"
            >{{ a.label }}</el-button>
            <el-button link @click="showDetail(row)">详情</el-button>
          </template>
        </el-table-column>
        <template #empty><el-empty description="暂无订单" /></template>
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

    <!-- 详情 -->
    <el-dialog v-model="detailVisible" title="订单详情" width="540px">
      <el-descriptions v-if="current" :column="1" border>
        <el-descriptions-item label="订单号">{{ current.order_no }}</el-descriptions-item>
        <el-descriptions-item label="状态"><StatusTag :status="current.status" /></el-descriptions-item>
        <el-descriptions-item label="客户">{{ current.customer_name }}（{{ current.contact_phone || '—' }}）</el-descriptions-item>
        <el-descriptions-item label="项目">{{ current.item_name }}</el-descriptions-item>
        <el-descriptions-item label="车辆">{{ current.plate_no }}</el-descriptions-item>
        <el-descriptions-item label="到店时间">{{ current.slot_date }} {{ current.start_time }}-{{ current.end_time }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ current.remark || '—' }}</el-descriptions-item>
        <el-descriptions-item v-if="current.reject_reason" label="拒绝原因">{{ current.reject_reason }}</el-descriptions-item>
        <el-descriptions-item v-if="current.service_note" label="服务记录">{{ current.service_note }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 操作弹窗（拒绝 / 完成） -->
    <el-dialog v-model="actionVisible" :title="actionTitle" width="460px">
      <el-form :model="actionForm" label-width="90px">
        <el-form-item v-if="actionTarget === 'rejected'" label="拒绝原因" required>
          <el-input v-model="actionForm.reason" type="textarea" :rows="3" placeholder="请说明拒绝原因，将展示给用户" />
        </el-form-item>
        <el-form-item v-if="actionTarget === 'completed'" label="服务记录">
          <el-input v-model="actionForm.service_note" type="textarea" :rows="3" placeholder="选填，如更换配件、建议下次保养时间等" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="actionVisible = false">取消</el-button>
        <el-button type="primary" :loading="acting" @click="confirmAction">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import StatusTag from '../../components/StatusTag.vue'
import { ORDER_STATUS_OPTIONS, STORE_ACTIONS } from '../../utils/format'
import { storeApi } from '../../api'

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

const actionVisible = ref(false)
const acting = ref(false)
const actionTarget = ref('')
const actionTitle = ref('')
const actionRow = ref(null)
const actionForm = reactive({ reason: '', service_note: '' })

function actions(row) {
  return STORE_ACTIONS[row.status] || []
}

async function load() {
  loading.value = true
  try {
    const data = await storeApi.orders({
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

function act(row, action) {
  if (action.needReason || action.status === 'completed') {
    actionRow.value = row
    actionTarget.value = action.status
    actionForm.reason = ''
    actionForm.service_note = ''
    actionTitle.value = action.status === 'rejected' ? '拒绝预约' : '完成服务'
    actionVisible.value = true
    return
  }
  ElMessageBox.confirm(`确定要「${action.label}」订单 ${row.order_no} 吗？`, '操作确认', { type: 'warning' })
    .then(() => doUpdate(row.id, { status: action.status }))
    .catch(() => {})
}

async function confirmAction() {
  if (actionTarget.value === 'rejected' && !actionForm.reason.trim()) {
    ElMessage.warning('请填写拒绝原因')
    return
  }
  acting.value = true
  try {
    await doUpdate(actionRow.value.id, {
      status: actionTarget.value,
      reason: actionForm.reason || null,
      service_note: actionForm.service_note || null
    })
    actionVisible.value = false
  } finally {
    acting.value = false
  }
}

async function doUpdate(id, payload) {
  try {
    await storeApi.orderStatus(id, payload)
    ElMessage.success('操作成功')
    load()
  } catch (e) {
    // 错误已由拦截器提示
  }
}

onMounted(load)
</script>
