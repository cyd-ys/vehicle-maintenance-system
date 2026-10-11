<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-brand">
        <span class="logo-mark" style="width: 44px; height: 44px; border-radius: 13px; display: grid; place-items: center; background: rgba(255, 255, 255, 0.2)">
          <el-icon :size="24"><Van /></el-icon>
        </span>
        <h1>汽车养护<br />预约服务系统</h1>
        <p class="sub">在线预约 · 时段校验 · 门店协同 · 全程可追溯</p>
        <ul>
          <li>浏览门店与养护项目，在线选择到店时段</li>
          <li>车辆档案统一管理，订单状态实时查询</li>
          <li>门店受理、拒绝、完成全流程数字化</li>
        </ul>
      </div>

      <div class="auth-form">
        <div style="display: flex; justify-content: flex-end">
          <ThemeToggle />
        </div>
        <h2>账号登录</h2>
        <p class="hint">支持使用用户名或注册邮箱登录</p>

        <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="onSubmit">
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="请输入用户名或邮箱" :prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" :prefix-icon="Lock" />
          </el-form-item>
          <el-button type="primary" :loading="loading" style="width: 100%; height: 42px" @click="onSubmit">
            登 录
          </el-button>
        </el-form>

        <div class="auth-tip" style="margin-top: 14px; font-size: 13px; color: var(--app-text-muted); display: flex; justify-content: space-between">
          <span>还没有账号？<router-link to="/register" class="brand-text">立即注册</router-link></span>
          <a class="brand-text" style="cursor: pointer" @click="openReset">忘记密码？</a>
        </div>

        <el-divider style="margin: 22px 0 16px">
          <span style="font-size: 12px; color: var(--app-text-muted)">一键填充演示账号</span>
        </el-divider>
        <div class="demo-accounts">
          <el-tag class="demo-tag" @click="fill('user1', 'user123')">普通用户　user1 / user123</el-tag>
          <el-tag type="success" class="demo-tag" @click="fill('store1', 'store123')">门店工作人员　store1 / store123</el-tag>
          <el-tag type="danger" class="demo-tag" @click="fill('admin', 'admin123')">系统管理员　admin / admin123</el-tag>
        </div>
      </div>
    </div>

    <!-- 通过邮箱验证码重置密码 -->
    <el-dialog v-model="resetVisible" title="重置密码" width="440px" append-to-body>
      <el-alert
        v-if="resetDebugCode"
        type="warning"
        :closable="false"
        show-icon
        style="margin-bottom: 14px"
        title="当前为本地调试模式"
        :description="`未配置 SMTP，验证码已自动填入：${resetDebugCode}`"
      />
      <el-form ref="resetRef" :model="resetForm" :rules="resetRules" label-position="top">
        <el-form-item label="注册邮箱" prop="email">
          <el-input v-model="resetForm.email" placeholder="请输入注册时使用的邮箱" :prefix-icon="Message" />
        </el-form-item>
        <el-form-item label="邮箱验证码" prop="code">
          <el-input v-model="resetForm.code" maxlength="6" placeholder="6 位数字验证码" :prefix-icon="Key">
            <template #append>
              <el-button :disabled="resetCounting > 0" :loading="resetSending" @click="onSendResetCode">
                {{ resetCounting > 0 ? `${resetCounting} 秒后重发` : '获取验证码' }}
              </el-button>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="resetForm.new_password" type="password" show-password placeholder="至少 6 位" :prefix-icon="Lock" />
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirm_password">
          <el-input v-model="resetForm.confirm_password" type="password" show-password placeholder="请再次输入新密码" :prefix-icon="Lock" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetVisible = false">取消</el-button>
        <el-button type="primary" :loading="resetSubmitting" @click="onResetSubmit">确认重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onBeforeUnmount, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Key, Lock, Message, User, Van } from '@element-plus/icons-vue'
import ThemeToggle from '../components/ThemeToggle.vue'
import { authApi } from '../api'
import { useAuthStore, homePathByRole } from '../store/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const formRef = ref()
const loading = ref(false)
const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名或邮箱', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

function fill(username, password) {
  form.username = username
  form.password = password
}

async function onSubmit() {
  await formRef.value.validate()
  loading.value = true
  try {
    const user = await auth.login({ ...form })
    ElMessage.success('登录成功')
    const redirect = route.query.redirect
    router.push(redirect || homePathByRole(user.role))
  } finally {
    loading.value = false
  }
}

/* ---------------- 忘记密码：邮箱验证码重置 ---------------- */
const resetVisible = ref(false)
const resetRef = ref()
const resetSending = ref(false)
const resetSubmitting = ref(false)
const resetCounting = ref(0)
const resetDebugCode = ref('')
const resetForm = reactive({ email: '', code: '', new_password: '', confirm_password: '' })

const EMAIL_RE = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/
const resetRules = {
  email: [
    { required: true, message: '请输入注册邮箱', trigger: 'blur' },
    { pattern: EMAIL_RE, message: '邮箱格式不正确', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入邮箱验证码', trigger: 'blur' },
    { pattern: /^\d{4,8}$/, message: '验证码为 4-8 位数字', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 64, message: '密码长度 6-64 位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule, value, cb) => (value === resetForm.new_password ? cb() : cb(new Error('两次输入的密码不一致'))),
      trigger: 'blur'
    }
  ]
}

let resetTimer = null

function openReset() {
  resetVisible.value = true
  resetForm.email = ''
  resetForm.code = ''
  resetForm.new_password = ''
  resetForm.confirm_password = ''
  resetDebugCode.value = ''
}

function startResetCountdown(seconds) {
  resetCounting.value = seconds
  clearInterval(resetTimer)
  resetTimer = setInterval(() => {
    resetCounting.value -= 1
    if (resetCounting.value <= 0) {
      clearInterval(resetTimer)
      resetCounting.value = 0
    }
  }, 1000)
}

onBeforeUnmount(() => clearInterval(resetTimer))

async function onSendResetCode() {
  try {
    await resetRef.value.validateField('email')
  } catch {
    return
  }
  resetSending.value = true
  try {
    const data = await authApi.sendEmailCode(resetForm.email.trim().toLowerCase(), 'reset')
    if (data?.debug_code) {
      resetDebugCode.value = data.debug_code
      resetForm.code = data.debug_code
      ElMessage.warning('SMTP 未配置，已启用本地调试模式，验证码已自动填入')
    } else {
      ElMessage.success(`验证码已发送至 ${resetForm.email}，${data?.expire_minutes ?? 5} 分钟内有效`)
    }
    startResetCountdown(data?.cooldown_seconds ?? 60)
  } catch {
    /* 错误提示已由 axios 拦截器统一处理 */
  } finally {
    resetSending.value = false
  }
}

async function onResetSubmit() {
  await resetRef.value.validate()
  resetSubmitting.value = true
  try {
    await authApi.resetPassword({
      email: resetForm.email.trim().toLowerCase(),
      code: resetForm.code.trim(),
      new_password: resetForm.new_password
    })
    ElMessage.success('密码已重置，请使用新密码登录')
    form.username = resetForm.email.trim().toLowerCase()
    form.password = resetForm.new_password
    resetVisible.value = false
  } finally {
    resetSubmitting.value = false
  }
}
</script>
