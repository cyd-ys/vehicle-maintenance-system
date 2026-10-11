import axios from 'axios'
import { ElMessage } from 'element-plus'

// 统一 axios 实例：注入 JWT 令牌、解包统一响应结构、处理鉴权失效
const service = axios.create({
  baseURL: '/api',
  timeout: 15000
})

service.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

service.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res && typeof res.code !== 'undefined') {
      if (res.code === 0) {
        return res.data
      }
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res
  },
  (error) => {
    // 完全没有响应体：请求根本没到达服务端（后端没启动 / 端口不通 / 被代理阻断）
    if (!error.response) {
      const reason = error.code === 'ECONNABORTED' ? '请求超时' : '无法连接后端服务'
      ElMessage.error(`${reason}，请确认后端已在 127.0.0.1:8000 运行（可双击项目根目录的 start-all.bat）`)
      return Promise.reject(error)
    }

    const status = error.response.status
    const message = error.response?.data?.message || error.message || '网络异常'
    if (status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      ElMessage.error('登录已过期，请重新登录')
      if (!location.pathname.startsWith('/login')) {
        location.href = '/login'
      }
    } else {
      ElMessage.error(message)
    }
    return Promise.reject(error)
  }
)

export default service
