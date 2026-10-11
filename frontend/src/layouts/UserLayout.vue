<template>
  <div class="user-shell">
    <header class="brand-bar">
      <div class="brand-logo">
        <span class="logo-mark">
          <el-icon :size="19"><Van /></el-icon>
        </span>
        <span>汽车养护预约服务系统</span>
      </div>

      <nav class="brand-nav">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          :class="{ 'nav-active': item.match(route.path) }"
        >
          {{ item.label }}
        </router-link>
      </nav>

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
              <el-dropdown-item divided command="profile">
                <el-icon><User /></el-icon>个人中心
              </el-dropdown-item>
              <el-dropdown-item command="logout">
                <el-icon><SwitchButton /></el-icon>退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <main class="page-container">
      <router-view v-slot="{ Component }">
        <transition name="fade-slide" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { Van, ArrowDown, User, SwitchButton } from '@element-plus/icons-vue'
import ThemeToggle from '../components/ThemeToggle.vue'
import UserAvatar from '../components/UserAvatar.vue'
import { useAuthStore } from '../store/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

// 自定义高亮规则：避免 router-link 默认的「前缀包含」匹配导致
// to="/user" 在所有 /user/* 页面都保持高亮
const navItems = [
  { label: '门店预约', to: '/user', match: (p) => p === '/user' || p.startsWith('/user/store') },
  { label: '我的车辆', to: '/user/vehicles', match: (p) => p.startsWith('/user/vehicles') },
  { label: '我的订单', to: '/user/orders', match: (p) => p.startsWith('/user/orders') },
  { label: '个人中心', to: '/user/profile', match: (p) => p.startsWith('/user/profile') }
]

function onCommand(command) {
  if (command === 'profile') {
    router.push('/user/profile')
  } else if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', { type: 'warning' })
      .then(() => {
        auth.logout()
        router.push('/login')
      })
      .catch(() => {})
  }
}
</script>
