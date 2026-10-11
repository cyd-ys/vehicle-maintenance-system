<template>
  <div>
    <div class="page-header">
      <h3 class="page-title">我的车辆</h3>
      <el-button type="primary" :icon="Plus" @click="openDialog()">新增车辆</el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="vehicles" v-loading="loading" stripe>
        <el-table-column prop="plate_no" label="车牌号" width="150">
          <template #default="{ row }">
            <el-tag :type="isNewEnergy(row.plate_no) ? 'success' : 'primary'" effect="dark" style="font-family: monospace; letter-spacing: 1px">
              {{ row.plate_no }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="brand" label="品牌" width="120" />
        <el-table-column prop="model" label="车型" width="140" />
        <el-table-column label="里程" width="120">
          <template #default="{ row }">{{ row.mileage ? row.mileage.toLocaleString() + ' 公里' : '—' }}</template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" show-overflow-tooltip />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="还没有车辆，点击右上角新增吧" />
        </template>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editId ? '编辑车辆' : '新增车辆'" width="520px" @closed="onClosed">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="车牌号" prop="plate_no">
          <PlateInput v-model="form.plate_no" />
        </el-form-item>

        <el-form-item label="品牌" prop="brand">
          <el-select
            v-model="form.brand"
            placeholder="选择或输入品牌"
            filterable
            allow-create
            default-first-option
            clearable
            style="width: 100%"
            @change="onBrandChange"
          >
            <el-option v-for="b in BRANDS" :key="b.name" :label="b.name" :value="b.name" />
          </el-select>
        </el-form-item>

        <el-form-item label="车型" prop="model">
          <el-select
            v-model="form.model"
            :placeholder="form.brand ? '选择或输入车型' : '请先选择品牌'"
            filterable
            allow-create
            default-first-option
            clearable
            style="width: 100%"
          >
            <el-option v-for="m in modelOptions" :key="m" :label="m" :value="m" />
          </el-select>
        </el-form-item>

        <el-form-item label="里程" prop="mileage">
          <el-input-number
            v-model="form.mileage"
            :min="0"
            :max="2000000"
            :step="1000"
            controls-position="right"
            style="width: 100%"
          />
          <div class="quick-row">
            <span class="text-muted">单位：公里　快捷填写</span>
            <el-tag
              v-for="m in MILEAGE_PRESETS"
              :key="m"
              size="small"
              effect="plain"
              class="quick-tag"
              @click="form.mileage = m"
            >{{ m.toLocaleString() }}</el-tag>
          </div>
        </el-form-item>

        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
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
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import PlateInput from '../../components/PlateInput.vue'
import { vehicleApi } from '../../api'
import { BRANDS, getModels, validatePlate } from '../../utils/plate'

const MILEAGE_PRESETS = [5000, 10000, 20000, 50000]

const vehicles = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const editId = ref(null)
const formRef = ref()
const form = reactive({ plate_no: '', brand: '', model: '', mileage: 0, remark: '' })

const modelOptions = computed(() => getModels(form.brand))

function isNewEnergy(plate) {
  return (plate || '').length === 8
}

const rules = {
  plate_no: [
    { required: true, message: '请输入车牌号', trigger: 'change' },
    {
      validator: (rule, value, cb) => {
        const r = validatePlate(value)
        return r.ok ? cb() : cb(new Error(r.message))
      },
      trigger: 'change'
    }
  ],
  brand: [{ required: true, message: '请选择或输入品牌', trigger: 'change' }],
  model: [{ required: true, message: '请选择或输入车型', trigger: 'change' }],
  mileage: [
    { required: true, message: '请输入里程', trigger: 'change' },
    { type: 'number', min: 0, max: 2000000, message: '里程需在 0 ~ 2000000 之间', trigger: 'change' }
  ]
}

async function load() {
  loading.value = true
  try {
    vehicles.value = await vehicleApi.list()
  } finally {
    loading.value = false
  }
}

function onBrandChange(brand) {
  // 品牌变更后，若原车型不属于新品牌则清空
  if (form.model && !getModels(brand).includes(form.model)) {
    form.model = ''
  }
}

function openDialog(row) {
  editId.value = row?.id || null
  Object.assign(
    form,
    row
      ? { plate_no: row.plate_no, brand: row.brand || '', model: row.model || '', mileage: row.mileage || 0, remark: row.remark || '' }
      : { plate_no: '', brand: '', model: '', mileage: 0, remark: '' }
  )
  dialogVisible.value = true
  formRef.value?.clearValidate?.()
}

function onClosed() {
  formRef.value?.clearValidate?.()
}

async function save() {
  await formRef.value.validate()
  saving.value = true
  try {
    const payload = { ...form, mileage: form.mileage ?? 0 }
    if (editId.value) {
      await vehicleApi.update(editId.value, payload)
      ElMessage.success('车辆信息已更新')
    } else {
      await vehicleApi.create(payload)
      ElMessage.success('车辆添加成功')
    }
    dialogVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

function remove(row) {
  ElMessageBox.confirm(`确定删除车辆 ${row.plate_no} 吗？`, '提示', { type: 'warning' })
    .then(async () => {
      await vehicleApi.remove(row.id)
      ElMessage.success('车辆已删除')
      load()
    })
    .catch(() => {})
}

onMounted(load)
</script>

<style scoped>
.quick-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 8px;
  width: 100%;
}
.quick-tag {
  cursor: pointer;
}
.quick-tag:hover {
  color: var(--brand);
  border-color: var(--brand);
}
</style>
