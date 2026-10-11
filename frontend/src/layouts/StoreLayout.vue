<template>
  <el-container style="height: 100vh">
    <el-aside width="228px" class="app-aside">
      <div class="app-aside-logo">
        <span class="logo-mark">
          <el-icon :size="18"><Shop /></el-icon>
        </span>
        <span>门店管理后台</span>
      </div>

      <el-menu :default-active="activeMenu" router class="app-menu">
        <el-menu-item index="/store">
          <el-icon><DataLine /></el-icon><span>经营概览</span>
        </el-menu-item>
        <el-menu-item index="/store/orders">
          <el-icon><List /></el-icon><span>预约订单</span>
        </el-menu-item>
        <el-menu-item index="/store/items">
          <el-icon><Tools /></el-icon><span>养护项目</span>
        </el-menu-item>
        <el-menu-item index="/store/slots">
          <el-icon><Calendar /></el-icon><span>服务时段</span>
        </el-menu-item>
        <el-menu-item index="/store/profile">
          <el-icon><Setting /></el-icon><span>门店资料</span>
        </el-menu-item>
        <el-menu-item index="/store/account">
          <el-icon><User /></el-icon><span>账号设置</span>
        </el-menu-item>
      </el-menu>

      <div class="app-aside-footer">
        汽车养护预约服务系统<br />
        <span style="opacity: 0.7">门店端 v1.0</span>
      </div>
    </el-aside>

    <el-container>
      <el-header class="app-topbar">
        <div class="app-topbar-title">{{ currentTitle }}</div>
        <div class="topbar-right">
          <ThemeToggle />
          <el-dropdown @command="onCommand">
            <span class="user-chip">
              <UserAvatar :user="auth.user" :size="26" />
              <span>{{ auth.user?.real_name || auth.user?.username }}</span>
              <el-icon :size="13" style="color: var(--app-text-muted)"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>{{ auth.roleText }}</el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { Shop, DataLine, List, Tools, Calendar, Setting, User, ArrowDown, SwitchButton } from '@element-plus/icons-vue'
import ThemeToggle from '../components/ThemeToggle.vue'
import UserAvatar from '../components/UserAvatar.vue'
import { useAuthStore } from '../store/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const activeMenu = computed(() => route.path)
const titles = {
  '/store': '经营概览',
  '/store/orders': '预约订单处理',
  '/store/items': '养护项目管理',
  '/store/slots': '服务时段配置',
  '/store/profile': '门店资料维护',
  '/store/account': '账号设置'
}
const currentTitle = computed(() => titles[route.path] || '门店管理后台')

function onCommand(command) {
  if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', { type: 'warning' })
      .then(() => {
        auth.logout()
        router.push('/login')
      })
      .catch(() => {})
  }
}
</script>
