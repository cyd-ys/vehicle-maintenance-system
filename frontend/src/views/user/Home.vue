<template>
  <div>
    <section class="hero">
      <h1>为爱车预约一次专业养护</h1>
      <p>浏览门店与养护项目，选择合适的到店时段，在线提交预约并实时查看订单状态。</p>
      <div style="position: relative; margin-top: 22px; display: flex; gap: 26px; flex-wrap: wrap">
        <div v-for="s in highlights" :key="s.label" style="display: flex; align-items: center; gap: 9px">
          <el-icon :size="19" style="opacity: 0.95"><component :is="s.icon" /></el-icon>
          <div>
            <div style="font-size: 19px; font-weight: 800; line-height: 1.2">{{ s.value }}</div>
            <div style="font-size: 12.5px; opacity: 0.85">{{ s.label }}</div>
          </div>
        </div>
      </div>
    </section>

    <div class="page-header">
      <h3 class="page-title">养护门店</h3>
      <el-input
        v-model="keyword"
        placeholder="搜索门店名称或地址"
        style="width: 300px"
        clearable
        @keyup.enter="load"
        @clear="load"
      >
        <template #append>
          <el-button :icon="Search" @click="load" />
        </template>
      </el-input>
    </div>

    <div v-loading="loading">
      <el-empty v-if="!stores.length && !loading" description="暂无可用门店" />
      <el-row :gutter="18">
        <el-col v-for="s in stores" :key="s.id" :xs="24" :sm="12" :md="8">
          <el-card class="store-card mb-12" shadow="hover" @click="goDetail(s.id)">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 10px">
              <div class="store-name">{{ s.name }}</div>
              <el-tag type="success" effect="light" round size="small">营业中</el-tag>
            </div>

            <div class="store-meta">
              <el-icon><Location /></el-icon>
              <span>{{ s.address || '地址待完善' }}</span>
            </div>
            <div class="store-meta">
              <el-icon><Phone /></el-icon>
              <span>{{ s.phone || '—' }}</span>
            </div>
            <div class="store-meta">
              <el-icon><Clock /></el-icon>
              <span>营业时间 {{ s.open_time }} - {{ s.close_time }}</span>
            </div>

            <div class="store-foot">
              <span>可约养护项目 <b style="color: var(--brand)">{{ s.item_count }}</b> 项</span>
              <el-button type="primary" size="small" @click.stop="goDetail(s.id)">立即预约</el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-pagination
        v-if="total > pageSize"
        class="mt-12"
        layout="prev, pager, next, total"
        :total="total"
        :page-size="pageSize"
        :current-page="page"
        @current-change="onPage"
      />
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Location, Phone, Clock, Shop, Tools, Timer } from '@element-plus/icons-vue'
import { catalogApi } from '../../api'

const router = useRouter()
const stores = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(9)
const keyword = ref('')
const loading = ref(false)

const highlights = ref([
  { icon: Shop, value: '—', label: '入驻门店' },
  { icon: Tools, value: '—', label: '养护项目' },
  { icon: Timer, value: '7 天', label: '可约时段' }
])

async function load() {
  loading.value = true
  try {
    const data = await catalogApi.stores({ page: page.value, page_size: pageSize.value, keyword: keyword.value })
    stores.value = data.items
    total.value = data.total
    const itemSum = stores.value.reduce((acc, s) => acc + (s.item_count || 0), 0)
    highlights.value[0].value = String(data.total)
    highlights.value[1].value = String(itemSum)
  } finally {
    loading.value = false
  }
}

function onPage(p) {
  page.value = p
  load()
}

function goDetail(id) {
  router.push(`/user/store/${id}`)
}

onMounted(load)
</script>
