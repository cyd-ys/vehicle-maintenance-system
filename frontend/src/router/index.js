import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore, homePathByRole } from '../store/auth'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'login', component: () => import('../views/Login.vue'), meta: { public: true } },
  { path: '/register', name: 'register', component: () => import('../views/Register.vue'), meta: { public: true } },

  // ---------------- 用户端 ----------------
  {
    path: '/user',
    component: () => import('../layouts/UserLayout.vue'),
    meta: { requiresAuth: true, roles: ['user'] },
    children: [
      { path: '', name: 'user-home', component: () => import('../views/user/Home.vue') },
      { path: 'store/:id', name: 'user-store', component: () => import('../views/user/StoreDetail.vue') },
      { path: 'vehicles', name: 'user-vehicles', component: () => import('../views/user/Vehicles.vue') },
      { path: 'orders', name: 'user-orders', component: () => import('../views/user/Orders.vue') },
      { path: 'profile', name: 'user-profile', component: () => import('../views/user/Profile.vue') }
    ]
  },

  // ---------------- 门店端 ----------------
  {
    path: '/store',
    component: () => import('../layouts/StoreLayout.vue'),
    meta: { requiresAuth: true, roles: ['store'] },
    children: [
      { path: '', name: 'store-dashboard', component: () => import('../views/store/Dashboard.vue') },
      { path: 'orders', name: 'store-orders', component: () => import('../views/store/Orders.vue') },
      { path: 'items', name: 'store-items', component: () => import('../views/store/Items.vue') },
      { path: 'slots', name: 'store-slots', component: () => import('../views/store/Slots.vue') },
      { path: 'profile', name: 'store-profile', component: () => import('../views/store/Profile.vue') },
      { path: 'account', name: 'store-account', component: () => import('../views/store/Account.vue') }
    ]
  },

  // ---------------- 管理端 ----------------
  {
    path: '/admin',
    component: () => import('../layouts/AdminLayout.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
    children: [
      { path: '', name: 'admin-dashboard', component: () => import('../views/admin/Dashboard.vue') },
      { path: 'users', name: 'admin-users', component: () => import('../views/admin/Users.vue') },
      { path: 'stores', name: 'admin-stores', component: () => import('../views/admin/Stores.vue') },
      { path: 'items', name: 'admin-items', component: () => import('../views/admin/Items.vue') },
      { path: 'orders', name: 'admin-orders', component: () => import('../views/admin/Orders.vue') },
      { path: 'logs', name: 'admin-logs', component: () => import('../views/admin/Logs.vue') },
      { path: 'account', name: 'admin-account', component: () => import('../views/admin/Account.vue') }
    ]
  },

  { path: '/:pathMatch(.*)*', redirect: '/login' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局路由守卫：未登录拦截 + 角色越权拦截（论文 1.2 / 3.5）
router.beforeEach((to) => {
  const auth = useAuthStore()

  if (to.meta.public) {
    if (auth.isLoggedIn && (to.name === 'login' || to.name === 'register')) {
      return homePathByRole(auth.role)
    }
    return true
  }

  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  const allowed = to.meta.roles
  if (allowed && !allowed.includes(auth.role)) {
    return homePathByRole(auth.role)
  }

  return true
})

export default router
