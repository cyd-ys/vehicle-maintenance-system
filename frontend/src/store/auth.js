import { defineStore } from 'pinia'
import { authApi } from '../api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null')
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    role: (state) => state.user?.role || '',
    roleText: (state) => ({ user: '普通用户', store: '门店工作人员', admin: '系统管理员' }[state.user?.role] || '')
  },
  actions: {
    setSession(token, user) {
      this.token = token
      this.user = user
      localStorage.setItem('token', token)
      localStorage.setItem('user', JSON.stringify(user))
    },
    async login(payload) {
      const data = await authApi.login(payload)
      this.setSession(data.access_token, data.user)
      return data.user
    },
    async register(payload) {
      return authApi.register(payload)
    },
    async fetchMe() {
      const user = await authApi.me()
      this.user = user
      localStorage.setItem('user', JSON.stringify(user))
      return user
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }
})

// 角色对应的首页路由
export function homePathByRole(role) {
  if (role === 'admin') return '/admin'
  if (role === 'store') return '/store'
  return '/user'
}
