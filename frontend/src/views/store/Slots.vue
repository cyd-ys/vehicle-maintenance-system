<template>
  <div>
    <div class="page-header">
      <h3 class="page-title">服务时段配置</h3>
      <div style="display: flex; gap: 10px">
        <el-button :icon="Plus" @click="singleVisible = true">新增单个时段</el-button>
        <el-button type="primary" :icon="MagicStick" @click="genVisible = true">批量生成时段</el-button>
      </div>
    </div>

    <el-card shadow="never">
      <div class="mb-12">
        <el-radio-group v-model="range" @change="load">
          <el-radio-button :value="3">近 3 天</el-radio-button>
          <el-radio-button :value="7">近 7 天</el-radio-button>
          <el-radio-button :value="30">近 30 天</el-radio-button>
          <el-radio-button :value="0">全部</el-radio-button>
        </el-radio-group>
      </div>

      <el-table :data="slots" v-loading="loading" stripe>
        <el-table-column prop="slot_date" label="日期" width="130" sortable />
        <el-table-column label="时段" width="160">
          <template #default="{ row }">{{ row.start_time }} - {{ row.end_time }}</template>
        </el-table-column>
        <el-table-column label="容量" width="90">
          <template #default="{ row }">{{ row.capacity }}</template>
        </el-table-column>
        <el-table-column label="已预约" width="90">
          <template #default="{ row }">{{ row.booked }}</template>
        </el-table-column>
        <el-table-column label="剩余" width="140">
          <template #default="{ row }">
            <el-tag :type="row.remaining > 0 ? 'success' : 'danger'" size="small">
              {{ row.remaining > 0 ? `剩余 ${row.remaining}` : '已约满' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty><el-empty description="暂未配置服务时段" /></template>
      </el-table>
    </el-card>

    <!-- 新增单个 -->
    <el-dialog v-model="singleVisible" title="新增单个时段" width="460px">
      <el-form ref="singleRef" :model="single" :rules="rules" label-width="90px">
        <el-form-item label="日期" prop="slot_date">
          <el-date-picker v-model="single.slot_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="开始时间" prop="start_time">
          <el-time-select v-model="single.start_time" start="06:00" step="00:30" end="22:00" style="width: 100%" />
        </el-form-item>
        <el-form-item label="结束时间" prop="end_time">
          <el-time-select v-model="single.end_time" start="06:00" step="00:30" end="22:00" style="width: 100%" />
        </el-form-item>
        <el-form-item label="容量" prop="capacity">
          <el-input-number v-model="single.capacity" :min="1" :max="999" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="singleVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveSingle">保存</el-button>
      </template>
    </el-dialog>

    <!-- 批量生成 -->
    <el-dialog v-model="genVisible" title="批量生成时段" width="540px">
      <el-form label-width="90px">
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="genDates"
            type="daterange"
            value-format="YYYY-MM-DD"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="时段区间">
          <div style="width: 100%">
            <div v-for="(r, i) in genRanges" :key="i" style="display: flex; gap: 8px; margin-bottom: 8px">
              <el-time-select v-model="r.start_time" start="06:00" step="00:30" end="22:00" style="flex: 1" placeholder="开始" />
              <el-time-select v-model="r.end_time" start="06:00" step="00:30" end="22:00" style="flex: 1" placeholder="结束" />
              <el-button :icon="Delete" circle plain type="danger" @click="genRanges.splice(i, 1)" />
            </div>
            <el-button :icon="Plus" plain @click="genRanges.push({ start_time: '', end_time: '' })">添加时段</el-button>
          </div>
        </el-form-item>
        <el-form-item label="每时段容量">
          <el-input-number v-model="genCapacity" :min="1" :max="999" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="genVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveGen">生成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, MagicStick } from '@element-plus/icons-vue'
import { storeApi } from '../../api'

const slots = ref([])
const loading = ref(false)
const range = ref(7)

const singleVisible = ref(false)
const singleRef = ref()
const saving = ref(false)
const single = reactive({ slot_date: '', start_time: '', end_time: '', capacity: 2 })
const rules = {
  slot_date: [{ required: true, message: '请选择日期', trigger: 'change' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_time: [{ required: true, message: '请选择结束时间', trigger: 'change' }]
}

const genVisible = ref(false)
const genDates = ref([])
const genRanges = ref([{ start_time: '09:00', end_time: '10:30' }, { start_time: '10:30', end_time: '12:00' }])
const genCapacity = ref(2)

function ymd(d) {
  const dt = new Date(d)
  const m = String(dt.getMonth() + 1).padStart(2, '0')
  const day = String(dt.getDate()).padStart(2, '0')
  return `${dt.getFullYear()}-${m}-${day}`
}

async function load() {
  loading.value = true
  try {
    const params = {}
    if (range.value > 0) {
      const start = new Date()
      const end = new Date()
      end.setDate(end.getDate() + range.value)
      params.start_date = ymd(start)
      params.end_date = ymd(end)
    }
    slots.value = await storeApi.slots(params)
  } finally {
    loading.value = false
  }
}

async function saveSingle() {
  await singleRef.value.validate()
  saving.value = true
  try {
    await storeApi.createSlot({ ...single })
    ElMessage.success('时段已新增')
    singleVisible.value = false
    single.slot_date = single.start_time = single.end_time = ''
    load()
  } finally {
    saving.value = false
  }
}

async function saveGen() {
  if (!genDates.value || genDates.value.length !== 2) {
    ElMessage.warning('请选择日期范围')
    return
  }
  const ranges = genRanges.value.filter((r) => r.start_time && r.end_time)
  if (!ranges.length) {
    ElMessage.warning('请至少配置一个完整时段')
    return
  }
  saving.value = true
  try {
    const res = await storeApi.generateSlots({
      start_date: genDates.value[0],
      end_date: genDates.value[1],
      capacity: genCapacity.value,
      ranges
    })
    ElMessage.success(`已生成 ${res.created} 个时段`)
    genVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

function remove(row) {
  ElMessageBox.confirm(`确定删除 ${row.slot_date} ${row.start_time}-${row.end_time} 时段吗？`, '提示', { type: 'warning' })
    .then(async () => {
      await storeApi.removeSlot(row.id)
      ElMessage.success('时段已删除')
      load()
    })
    .catch(() => {})
}

onMounted(load)
</script>
