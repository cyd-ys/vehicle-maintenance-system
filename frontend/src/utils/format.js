// 订单状态显示与标签颜色（论文 4.5 订单状态机）
export const ORDER_STATUS = {
  pending: { text: '待受理', type: 'warning' },
  confirmed: { text: '已确认', type: 'primary' },
  in_service: { text: '服务中', type: 'info' },
  completed: { text: '已完成', type: 'success' },
  cancelled: { text: '已取消', type: 'info' },
  rejected: { text: '已拒绝', type: 'danger' }
}

export const ORDER_STATUS_OPTIONS = Object.entries(ORDER_STATUS).map(([value, cfg]) => ({
  value,
  label: cfg.text
}))

export const STORE_STATUS = {
  0: { text: '待审核', type: 'warning' },
  1: { text: '正常营业', type: 'success' },
  2: { text: '已停用', type: 'danger' }
}

export const USER_ROLE = {
  user: '普通用户',
  store: '门店工作人员',
  admin: '系统管理员'
}

export function orderStatusText(status) {
  return ORDER_STATUS[status]?.text || status
}

export function formatMoney(value) {
  const num = Number(value || 0)
  return `¥${num.toFixed(2)}`
}

// 门店端可用操作（依据状态机）
export const STORE_ACTIONS = {
  pending: [
    { status: 'confirmed', label: '确认受理', type: 'primary' },
    { status: 'rejected', label: '拒绝', type: 'danger', needReason: true }
  ],
  confirmed: [{ status: 'in_service', label: '开始服务', type: 'primary' }],
  in_service: [{ status: 'completed', label: '完成服务', type: 'success' }]
}
