<template>
  <div v-loading="loading">
    <h3 class="page-title mb-12">平台概览</h3>
    <el-row :gutter="16" class="mb-12">
      <el-col v-for="c in cards" :key="c.label" :xs="12" :md="6">
        <el-card shadow="never" class="stat-card mb-12">
          <el-icon class="stat-icon"><component :is="c.icon" /></el-icon>
          <div class="stat-value" :style="c.color ? { color: c.color } : {}">{{ c.value }}</div>
          <div class="stat-label">{{ c.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :md="14">
        <el-card shadow="never" class="mb-12">
          <template #header>
            <b>订单状态分布</b>
            <span class="text-muted" style="margin-left: 8px">共 {{ stats.order_count || 0 }} 单</span>
          </template>
          <el-row :gutter="12">
            <el-col v-for="(v, k) in stats.by_status" :key="k" :span="8" style="margin-bottom: 12px">
              <div class="mini-stat">
                <span class="mini-dot" :class="'dot-' + k"></span>
                <span>{{ ORDER_STATUS[k]?.text || k }}</span>
                <b>{{ v }}</b>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="10">
        <el-card shadow="never">
          <template #header><b>管理快捷入口</b></template>
          <el-space direction="vertical" fill style="width: 100%">
            <el-button style="width: 100%" @click="$router.push('/admin/stores')">
              <el-icon><Shop /></el-icon>&nbsp;门店审核（待审核 {{ stats.pending_store_count ?? 0 }} 家）
            </el-button>
            <el-button style="width: 100%" @click="$router.push('/admin/users')">
              <el-icon><UserFilled /></el-icon>&nbsp;用户与账号管理
            </el-button>
            <el-button style="width: 100%" @click="$router.push('/admin/items')">
              <el-icon><Tools /></el-icon>&nbsp;养护项目合规管理
            </el-button>
            <el-button style="width: 100%" @click="$router.push('/admin/logs')">
              <el-icon><Document /></el-icon>&nbsp;查看关键操作日志
            </el-button>
          </el-space>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { UserFilled, Shop, Tickets, Stamp } from '@element-plus/icons-vue'
import { adminApi } from '../../api'
import { ORDER_STATUS } from '../../utils/format'

const loading = ref(false)
const stats = ref({})

const cards = computed(() => {
  const pendingStores = stats.value.pending_store_count ?? 0
  return [
    { label: '注册用户', value: stats.value.user_count ?? 0, icon: UserFilled },
    { label: '入驻门店', value: stats.value.store_count ?? 0, icon: Shop },
    { label: '累计订单', value: stats.value.order_count ?? 0, icon: Tickets },
    {
      label: '待审核门店',
      value: pendingStores,
      icon: Stamp,
      color: pendingStores > 0 ? '#e6a23c' : undefined
    }
  ]
})

async function load() {
  loading.value = true
  try {
    stats.value = await adminApi.stats()
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
