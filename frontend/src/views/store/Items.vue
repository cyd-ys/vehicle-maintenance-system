<template>
  <div>
    <div class="page-header">
      <h3 class="page-title">养护项目管理</h3>
      <el-button type="primary" :icon="Plus" @click="openDialog()">新增项目</el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="items" v-loading="loading" stripe>
        <el-table-column prop="name" label="项目名称" min-width="150" />
        <el-table-column prop="category" label="类别" width="110" />
        <el-table-column label="服务时长" width="110">
          <template #default="{ row }">{{ row.duration }} 分钟</template>
        </el-table-column>
        <el-table-column label="参考价格" width="110">
          <template #default="{ row }">¥{{ Number(row.price).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="description" label="说明" show-overflow-tooltip />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
              {{ row.status === 1 ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button link type="info" @click="remove(row)">停用</el-button>
          </template>
        </el-table-column>
        <template #empty><el-empty description="暂无养护项目" /></template>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editId ? '编辑项目' : '新增项目'" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="form.name" placeholder="如 机油机滤更换" />
        </el-form-item>
        <el-form-item label="类别" prop="category">
          <el-input v-model="form.category" placeholder="如 常规保养" />
        </el-form-item>
        <el-form-item label="服务时长" prop="duration">
          <el-input-number v-model="form.duration" :min="10" :max="1440" :step="10" style="width: 100%" />
          <span class="text-muted">分钟</span>
        </el-form-item>
        <el-form-item label="参考价格" prop="price">
          <el-input-number v-model="form.price" :min="0" :precision="2" :step="10" style="width: 100%" />
        </el-form-item>
        <el-form-item label="项目说明">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" active-text="启用" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { storeApi } from '../../api'

const items = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const editId = ref(null)
const formRef = ref()
const form = reactive({ name: '', category: '', duration: 60, price: 0, description: '', status: 1 })

const rules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
  duration: [{ required: true, message: '请设置服务时长', trigger: 'blur' }],
  price: [{ required: true, message: '请设置价格', trigger: 'blur' }]
}

async function load() {
  loading.value = true
  try {
    items.value = await storeApi.items()
  } finally {
    loading.value = false
  }
}

function openDialog(row) {
  editId.value = row?.id || null
  Object.assign(form, row
    ? { name: row.name, category: row.category, duration: row.duration, price: Number(row.price), description: row.description, status: row.status }
    : { name: '', category: '', duration: 60, price: 0, description: '', status: 1 })
  dialogVisible.value = true
}

async function save() {
  await formRef.value.validate()
  saving.value = true
  try {
    if (editId.value) {
      await storeApi.updateItem(editId.value, { ...form })
      ElMessage.success('项目已更新')
    } else {
      await storeApi.createItem({ ...form })
      ElMessage.success('项目已新增')
    }
    dialogVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

function remove(row) {
  ElMessageBox.confirm(`确定停用「${row.name}」吗？停用后用户将无法预约该项目，历史订单不受影响。`, '提示', { type: 'warning' })
    .then(async () => {
      await storeApi.removeItem(row.id)
      ElMessage.success('项目已停用')
      load()
    })
    .catch(() => {})
}

onMounted(load)
</script>
