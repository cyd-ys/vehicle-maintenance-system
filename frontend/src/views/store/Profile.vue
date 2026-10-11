<template>
  <div v-loading="loading">
    <h3 class="page-title mb-12">门店资料维护</h3>
    <el-card shadow="never" style="max-width: 720px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
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
            <el-time-select v-model="form.open_time" start="06:00" step="00:30" end="23:00" style="width: 140px" />
            <span>至</span>
            <el-time-select v-model="form.close_time" start="06:00" step="00:30" end="23:59" style="width: 140px" />
          </div>
        </el-form-item>
        <el-form-item label="门店简介">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="当前状态">
          <el-tag :type="statusCfg.type">{{ statusCfg.text }}</el-tag>
          <span class="text-muted" style="margin-left: 10px">（状态由平台管理员审核维护）</span>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="save">保存资料</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { storeApi } from '../../api'
import { STORE_STATUS } from '../../utils/format'

const loading = ref(false)
const saving = ref(false)
const formRef = ref()
const form = reactive({ name: '', address: '', phone: '', open_time: '09:00', close_time: '18:00', description: '', status: 1 })

const rules = {
  name: [{ required: true, message: '请输入门店名称', trigger: 'blur' }],
  phone: [{ pattern: /^[\d-]{6,20}$/, message: '电话格式不正确', trigger: 'blur' }]
}

const statusCfg = computed(() => STORE_STATUS[form.status] || { text: '未知', type: 'info' })

async function load() {
  loading.value = true
  try {
    const data = await storeApi.profile()
    Object.assign(form, data)
  } finally {
    loading.value = false
  }
}

async function save() {
  await formRef.value.validate()
  saving.value = true
  try {
    await storeApi.updateProfile({
      name: form.name, address: form.address, phone: form.phone,
      open_time: form.open_time, close_time: form.close_time, description: form.description
    })
    ElMessage.success('门店资料已更新')
    load()
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
