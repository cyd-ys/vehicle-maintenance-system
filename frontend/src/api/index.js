import request from './request'

// ---------------- 认证 ----------------
export const authApi = {
  // 发送邮箱验证码：purpose 取 'register' | 'reset'
  sendEmailCode: (email, purpose = 'register') => request.post('/auth/email/code', { email, purpose }),
  register: (data) => request.post('/auth/register', data),
  resetPassword: (data) => request.post('/auth/password/reset', data),
  login: (data) => request.post('/auth/login', data),
  me: () => request.get('/auth/me'),
  updateProfile: (data) => request.put('/auth/me', data),
  changePassword: (data) => request.put('/auth/me/password', data),
  // 更换绑定邮箱（需先向新邮箱获取验证码）
  sendChangeEmailCode: (email) => request.post('/auth/me/email/code', { email }),
  changeEmail: (data) => request.put('/auth/me/email', data),
  // 头像：上传（multipart）与恢复默认
  // 注意：不要手动指定 Content-Type，浏览器需要自己补上 multipart 的 boundary
  uploadAvatar: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return request.post('/auth/me/avatar', fd)
  },
  resetAvatar: () => request.delete('/auth/me/avatar')
}

// ---------------- 车辆 ----------------
export const vehicleApi = {
  list: () => request.get('/vehicles'),
  create: (data) => request.post('/vehicles', data),
  update: (id, data) => request.put(`/vehicles/${id}`, data),
  remove: (id) => request.delete(`/vehicles/${id}`)
}

// ---------------- 门店与项目（用户端浏览） ----------------
export const catalogApi = {
  stores: (params) => request.get('/stores', { params }),
  storeDetail: (id) => request.get(`/stores/${id}`),
  storeItems: (id) => request.get(`/stores/${id}/items`),
  slots: (params) => request.get('/slots', { params })
}

// ---------------- 预约订单（用户端） ----------------
export const reservationApi = {
  create: (data) => request.post('/reservations', data),
  list: (params) => request.get('/reservations', { params }),
  detail: (id) => request.get(`/reservations/${id}`),
  cancel: (id) => request.patch(`/reservations/${id}/status`, { status: 'cancelled' })
}

// ---------------- 门店端 ----------------
export const storeApi = {
  profile: () => request.get('/store/profile'),
  updateProfile: (data) => request.put('/store/profile', data),
  items: () => request.get('/store/items'),
  createItem: (data) => request.post('/store/items', data),
  updateItem: (id, data) => request.put(`/store/items/${id}`, data),
  removeItem: (id) => request.delete(`/store/items/${id}`),
  slots: (params) => request.get('/store/slots', { params }),
  createSlot: (data) => request.post('/store/slots', data),
  removeSlot: (id) => request.delete(`/store/slots/${id}`),
  generateSlots: (data) => request.post('/store/slots/generate', data),
  orders: (params) => request.get('/store/orders', { params }),
  orderStatus: (id, data) => request.patch(`/store/orders/${id}/status`, data),
  stats: () => request.get('/store/stats')
}

// ---------------- 管理端 ----------------
export const adminApi = {
  users: (params) => request.get('/admin/users', { params }),
  userStatus: (id, status) => request.put(`/admin/users/${id}/status`, { status }),
  stores: (params) => request.get('/admin/stores', { params }),
  createStore: (data) => request.post('/admin/stores', data),
  reviewStore: (id, status) => request.put(`/admin/stores/${id}/review`, { status }),
  items: (params) => request.get('/admin/items', { params }),
  itemStatus: (id, status) => request.put(`/admin/items/${id}/status`, { status }),
  orders: (params) => request.get('/admin/orders', { params }),
  logs: (params) => request.get('/admin/logs', { params }),
  stats: () => request.get('/admin/stats')
}
