<template>
  <div v-loading="loading">
    <h3 class="page-title mb-12">经营概览</h3>
    <el-row :gutter="16" class="mb-12">
      <el-col v-for="c in cards" :key="c.label" :xs="12" :md="6">
        <el-card shadow="never" class="stat-card mb-12">
          <el-icon class="stat-icon"><component :is="c.icon" /></el-icon>
          <div class="stat-value">{{ c.value }}</div>
          <div class="stat-label">{{ c.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :md="14">
        <el-card shadow="never" class="mb-12">
          <template #header>
            <b>订单状态分布</b>
            <span class="text-muted" style="margin-left: 8px">共 {{ stats.total_orders || 0 }} 单</span>
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
          <template #header><b>快捷入口</b></template>
          <el-space direction="vertical" fill style="width: 100%">
            <el-button style="width: 100%" @click="$router.push('/store/orders')">
              <el-icon><List /></el-icon>&nbsp;处理预约订单（待受理 {{ stats.pending ?? 0 }} 单）
            </el-button>
            <el-button style="width: 100%" @click="$router.push('/store/items')">
              <el-icon><Tools /></el-icon>&nbsp;维护养护项目（{{ stats.item_count || 0 }} 项）
            </el-button>
            <el-button style="width: 100%" @click="$router.push('/store/slots')">
              <el-icon><Calendar /></el-icon>&nbsp;配置服务时段
            </el-button>
          </el-space>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Tickets, Calendar, Bell, Wallet, List, Tools } from '@element-plus/icons-vue'
import { storeApi } from '../../api'
import { ORDER_STATUS } from '../../utils/format'

const loading = ref(false)
const stats = ref({})

const cards = computed(() => [
  { label: '累计订单', value: stats.value.total_orders ?? 0, icon: Tickets },
  { label: '今日预约', value: stats.value.today_orders ?? 0, icon: Calendar },
  { label: '待受理', value: stats.value.pending ?? 0, icon: Bell },
  { label: '已完成营收', value: `¥${Number(stats.value.completed_revenue || 0).toFixed(0)}`, icon: Wallet }
])

async function load() {
  loading.value = true
  try {
    const data = await storeApi.stats()
    stats.value = { ...data, pending: data.by_status?.pending || 0 }
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
