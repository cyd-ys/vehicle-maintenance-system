import axios from 'axios'
import { ElMessage } from 'element-plus'

// 统一 axios 实例：注入 JWT 令牌、解包统一响应结构、处理鉴权失效
const service = axios.create({
  baseURL: '/api',
  timeout: 15000
})

// 令牌同时挂在自定义头和标准 Authorization 头上。
// 原因：部分反向代理（例如发布平台的网关）会补写/改写 Authorization 请求头，
// 客户端携带的令牌会被覆盖，表现为「登录成功但所有鉴权接口都 401」。
// 后端因此优先读取 X-Auth-Token，标准头只用于兼容本地开发与 Swagger 调试。
function attachToken(config, token) {
  if (!config.headers) config.headers = {}
  if (typeof config.headers.set === 'function') {
    config.headers.set('X-Auth-Token', token)
    config.headers.set('Authorization', `Bearer ${token}`)
  } else {
    config.headers['X-Auth-Token'] = token
    config.headers.Authorization = `Bearer ${token}`
  }
}

service.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      attachToken(config, token)
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
  async (error) => {
    let err = error
    const config = err.config || {}

    // 自愈重试：万一连自定义头也被网关过滤掉，就改用查询参数把请求重发一次。
    // 只重试一次（__tokenRetried 标记），避免死循环。
    if (err.response && err.response.status === 401 && !config.__tokenRetried) {
      const token = localStorage.getItem('token')
      if (token) {
        config.__tokenRetried = true
        config.params = { ...(config.params || {}), access_token: token }
        attachToken(config, token)
        try {
          return await service.request(config)
        } catch (retryError) {
          // 重试仍失败：内层拦截器已经提示并跳转过，这里标记后直接抛出，避免重复弹窗
          if (retryError && typeof retryError === 'object') retryError.__handled = true
          err = retryError
        }
      }
    }
    if (err && err.__handled) return Promise.reject(err)

    // 完全没有响应体：请求根本没到达服务端（后端没启动 / 端口不通 / 被代理阻断）
    if (!err.response) {
      const reason = err.code === 'ECONNABORTED' ? '请求超时' : '无法连接后端服务'
      // 线上是单端口部署（前后端同源），本地开发才是 8000 + 5173 两个端口
      const dev = ['localhost', '127.0.0.1'].includes(location.hostname) && location.port === '5173'
      const hint = dev
        ? '（可双击项目根目录的 start-all.bat 后重试）'
        : '，请稍后重试'
      ElMessage.error(`${reason}${hint}`)
      return Promise.reject(err)
    }

    const status = err.response.status
    const message = err.response?.data?.message || err.message || '网络异常'
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
    return Promise.reject(err)
  }
)

export default service
