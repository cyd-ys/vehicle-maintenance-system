<template>
  <div v-loading="loading">
    <el-page-header content="返回门店列表" @back="$router.push('/user')" style="margin-bottom: 16px" />

    <el-card v-if="store" shadow="never" class="mb-12">
      <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 12px">
        <div>
          <h2 style="margin: 0 0 8px">{{ store.name }}</h2>
          <div class="text-muted">
            <el-icon><Location /></el-icon> {{ store.address || '地址待完善' }}
          </div>
          <div class="text-muted" style="margin-top: 4px">
            <el-icon><Clock /></el-icon> 营业时间 {{ store.open_time }} - {{ store.close_time }}
            &nbsp;｜&nbsp; <el-icon><Phone /></el-icon> {{ store.phone || '—' }}
          </div>
          <p class="text-muted" style="margin: 10px 0 0">{{ store.description }}</p>
        </div>
        <el-tag type="success" size="large" effect="light">营业中</el-tag>
      </div>
    </el-card>

    <h3 class="page-title mb-12">养护项目</h3>
    <el-empty v-if="!items.length && !loading" description="该门店暂无可预约项目" />
    <el-row :gutter="16">
      <el-col v-for="it in items" :key="it.id" :xs="24" :sm="12" :md="8">
        <el-card shadow="hover" class="mb-12">
          <div style="display: flex; justify-content: space-between">
            <div style="font-weight: 600">{{ it.name }}</div>
            <el-tag size="small" effect="plain">{{ it.category || '养护' }}</el-tag>
          </div>
          <div class="text-muted" style="margin: 8px 0">
            <el-icon><Timer /></el-icon> 预计 {{ it.duration }} 分钟
          </div>
          <p class="text-muted" style="min-height: 40px">{{ it.description }}</p>
          <div style="display: flex; justify-content: space-between; align-items: center">
            <span class="price-tag">¥{{ Number(it.price).toFixed(2) }}</span>
            <el-button type="primary" @click="openBooking(it)">立即预约</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 预约弹窗 -->
    <el-dialog v-model="dialogVisible" title="提交预约" width="560px" @closed="resetForm">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="养护项目">
          <el-input :value="currentItem?.name" disabled />
        </el-form-item>
        <el-form-item label="选择车辆" prop="vehicle_id">
          <el-select v-model="form.vehicle_id" placeholder="请选择车辆" style="width: 100%">
            <el-option
              v-for="v in vehicles"
              :key="v.id"
              :label="`${v.plate_no}（${v.brand || ''} ${v.model || ''}）`"
              :value="v.id"
            />
          </el-select>
          <div v-if="!vehicles.length" class="text-muted" style="margin-top: 6px">
            还没有车辆，请先前往 <router-link to="/user/vehicles">我的车辆</router-link> 添加
          </div>
        </el-form-item>
        <el-form-item label="到店日期" prop="date">
          <el-date-picker
            v-model="form.date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择日期"
            :disabled-date="disabledDate"
            style="width: 100%"
            @change="loadSlots"
          />
        </el-form-item>
        <el-form-item label="服务时段" prop="slot_id">
          <div v-loading="slotLoading" style="width: 100%">
            <el-empty v-if="form.date && !slots.length && !slotLoading" description="当日暂无可预约时段" :image-size="60" />
            <el-radio-group v-model="form.slot_id" v-if="slots.length">
              <el-radio-button
                v-for="s in slots"
                :key="s.id"
                :value="s.id"
                :disabled="s.remaining <= 0"
                style="margin: 0 8px 8px 0"
              >
                {{ s.start_time }}-{{ s.end_time }}
                <span class="text-muted">（余 {{ s.remaining }}）</span>
              </el-radio-button>
            </el-radio-group>
          </div>
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="form.contact_name" placeholder="选填" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="form.contact_phone" placeholder="选填，便于门店联系" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="选填，如指定配件、到店提醒等" />
        </el-form-item>
        <el-alert v-if="currentItem" type="info" :closable="false" show-icon
          :title="`服务时长约 ${currentItem.duration} 分钟，费用 ¥${Number(currentItem.price).toFixed(2)}`" />
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">确认预约</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Location, Phone, Clock, Timer } from '@element-plus/icons-vue'
import { catalogApi, reservationApi, vehicleApi } from '../../api'

const route = useRoute()
const router = useRouter()
const storeId = Number(route.params.id)

const store = ref(null)
const items = ref([])
const vehicles = ref([])
const loading = ref(false)

const dialogVisible = ref(false)
const currentItem = ref(null)
const slots = ref([])
const slotLoading = ref(false)
const submitting = ref(false)
const formRef = ref()

const form = reactive({ vehicle_id: null, date: '', slot_id: null, contact_name: '', contact_phone: '', remark: '' })
const rules = {
  vehicle_id: [{ required: true, message: '请选择车辆', trigger: 'change' }],
  date: [{ required: true, message: '请选择到店日期', trigger: 'change' }],
  slot_id: [{ required: true, message: '请选择服务时段', trigger: 'change' }]
}

function disabledDate(d) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const max = new Date(today)
  max.setDate(max.getDate() + 30)
  return d < today || d > max
}

async function loadBase() {
  loading.value = true
  try {
    const [s, its, vs] = await Promise.all([
      catalogApi.storeDetail(storeId),
      catalogApi.storeItems(storeId),
      vehicleApi.list().catch(() => [])
    ])
    store.value = s
    items.value = its
    vehicles.value = vs
  } catch (e) {
    // 门店不存在或已停用时，回退到列表
    router.replace('/user')
  } finally {
    loading.value = false
  }
}

function openBooking(item) {
  currentItem.value = item
  dialogVisible.value = true
}

function resetForm() {
  form.vehicle_id = vehicles.value[0]?.id || null
  form.date = ''
  form.slot_id = null
  form.contact_name = ''
  form.contact_phone = ''
  form.remark = ''
  slots.value = []
}

async function loadSlots() {
  form.slot_id = null
  if (!form.date) return
  slotLoading.value = true
  try {
    slots.value = await catalogApi.slots({ store_id: storeId, date: form.date })
  } finally {
    slotLoading.value = false
  }
}

async function submit() {
  await formRef.value.validate()
  submitting.value = true
  try {
    await reservationApi.create({
      vehicle_id: form.vehicle_id,
      store_id: storeId,
      item_id: currentItem.value.id,
      slot_id: form.slot_id,
      contact_name: form.contact_name || null,
      contact_phone: form.contact_phone || null,
      remark: form.remark || null
    })
    ElMessage.success('预约提交成功，请等待门店受理')
    dialogVisible.value = false
    router.push('/user/orders')
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await loadBase()
  resetForm()
})
</script>
