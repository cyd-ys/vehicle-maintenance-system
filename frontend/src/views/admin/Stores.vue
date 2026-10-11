<template>
  <div>
    <div class="page-header">
      <h3 class="page-title">门店管理</h3>
      <div style="display: flex; gap: 10px">
        <el-input v-model="keyword" placeholder="搜索门店名称/地址" style="width: 220px" clearable @keyup.enter="reload" @clear="reload" />
        <el-select v-model="status" placeholder="全部状态" style="width: 150px" clearable @change="reload">
          <el-option label="待审核" :value="0" />
          <el-option label="正常营业" :value="1" />
          <el-option label="已停用" :value="2" />
        </el-select>
        <el-button type="primary" :icon="Plus" @click="openCreate">新增门店</el-button>
      </div>
    </div>

    <el-card shadow="never">
      <el-table :data="stores" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="门店名称" min-width="160" />
        <el-table-column prop="address" label="地址" show-overflow-tooltip />
        <el-table-column prop="phone" label="电话" width="140" />
        <el-table-column label="营业时间" width="130">
          <template #default="{ row }">{{ row.open_time }}-{{ row.close_time }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="STORE_STATUS[row.status]?.type" size="small">{{ STORE_STATUS[row.status]?.text }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status !== 1" link type="success" @click="review(row, 1)">通过</el-button>
            <el-button v-if="row.status !== 2" link type="danger" @click="review(row, 2)">停用</el-button>
            <el-button link @click="showDetail(row)">详情</el-button>
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

    <!-- 新增门店 -->
    <el-dialog v-model="createVisible" title="新增门店" width="560px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
        <el-divider content-position="left">门店信息</el-divider>
        <el-form-item label="门店名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="门店地址" prop="address">
          <el-input v-model="form.address" />
        </el-form-item>
        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="营业时间">
          <div style="display: flex; gap: 8px; align-items: center">
            <el-time-select v-model="form.open_time" start="06:00" step="00:30" end="23:00" style="width: 130px" />
            <span>至</span>
            <el-time-select v-model="form.close_time" start="06:00" step="00:30" end="23:59" style="width: 130px" />
          </div>
        </el-form-item>
        <el-form-item label="门店简介">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="初始状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">审核通过</el-radio>
            <el-radio :value="0">待审核</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-divider content-position="left">门店登录账号（选填）</el-divider>
        <el-form-item label="账号用户名" prop="username">
          <el-input v-model="form.username" placeholder="留空则不创建门店账号" />
        </el-form-item>
        <el-form-item label="账号密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="留空则使用默认密码 store123" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="detailVisible" title="门店详情" width="520px">
      <el-descriptions v-if="current" :column="1" border>
        <el-descriptions-item label="门店名称">{{ current.name }}</el-descriptions-item>
        <el-descriptions-item label="地址">{{ current.address || '—' }}</el-descriptions-item>
        <el-descriptions-item label="电话">{{ current.phone || '—' }}</el-descriptions-item>
        <el-descriptions-item label="营业时间">{{ current.open_time }} - {{ current.close_time }}</el-descriptions-item>
        <el-descriptions-item label="简介">{{ current.description || '—' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="STORE_STATUS[current.status]?.type" size="small">{{ STORE_STATUS[current.status]?.text }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="入驻时间">{{ current.created_at }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { adminApi } from '../../api'
import { STORE_STATUS } from '../../utils/format'

const stores = ref([])
const loading = ref(false)
const status = ref('')
const keyword = ref('')
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

const createVisible = ref(false)
const saving = ref(false)
const formRef = ref()
const form = reactive({
  name: '', address: '', phone: '', description: '',
  open_time: '09:00', close_time: '18:00', status: 1, username: '', password: ''
})
const rules = {
  name: [{ required: true, message: '请输入门店名称', trigger: 'blur' }],
  username: [{ min: 3, message: '用户名至少 3 位', trigger: 'blur' }],
  password: [{ min: 6, message: '密码至少 6 位', trigger: 'blur' }]
}

const detailVisible = ref(false)
const current = ref(null)

async function load() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (status.value !== '' && status.value !== undefined && status.value !== null) params.status = status.value
    if (keyword.value) params.keyword = keyword.value
    const data = await adminApi.stores(params)
    stores.value = data.items
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

function openCreate() {
  Object.assign(form, {
    name: '', address: '', phone: '', description: '',
    open_time: '09:00', close_time: '18:00', status: 1, username: '', password: ''
  })
  createVisible.value = true
}

async function save() {
  await formRef.value.validate()
  saving.value = true
  try {
    const payload = { ...form }
    if (!payload.username) {
      delete payload.username
      delete payload.password
    } else if (!payload.password) {
      payload.password = 'store123'
    }
    await adminApi.createStore(payload)
    ElMessage.success('门店创建成功')
    createVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

function review(row, target) {
  const word = target === 1 ? '通过审核' : '停用'
  ElMessageBox.confirm(`确定${word}门店「${row.name}」吗？`, '提示', { type: 'warning' })
    .then(async () => {
      await adminApi.reviewStore(row.id, target)
      ElMessage.success(`门店已${word}`)
      load()
    })
    .catch(() => {})
}

function showDetail(row) {
  current.value = row
  detailVisible.value = true
}

onMounted(load)
</script>
