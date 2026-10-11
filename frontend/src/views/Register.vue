<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-brand">
        <span class="logo-mark" style="width: 44px; height: 44px; border-radius: 13px; display: grid; place-items: center; background: rgba(255, 255, 255, 0.2)">
          <el-icon :size="24"><Van /></el-icon>
        </span>
        <h1>加入我们<br />开启在线养护</h1>
        <p class="sub">注册后即可浏览门店、管理车辆并在线预约养护服务。</p>
        <ul>
          <li>邮箱验证码注册，账号安全可追溯</li>
          <li>一个账号管理多辆爱车档案</li>
          <li>实时查看可用时段，避免白跑一趟</li>
          <li>订单状态全程可查，服务进度透明</li>
        </ul>
      </div>

      <div class="auth-form">
        <div style="display: flex; justify-content: flex-end">
          <ThemeToggle />
        </div>
        <h2>注册新账号</h2>
        <p class="hint">使用邮箱接收验证码完成注册</p>

        <el-alert
          v-if="debugCode"
          type="warning"
          :closable="false"
          show-icon
          style="margin-bottom: 14px"
          title="当前为本地调试模式"
          :description="`未配置 SMTP，验证码已自动填入：${debugCode}`"
        />

        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" size="large">
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="form.email" placeholder="用于接收验证码，如 name@example.com" :prefix-icon="Message" />
          </el-form-item>

          <el-form-item label="邮箱验证码" prop="code">
            <el-input v-model="form.code" maxlength="6" placeholder="6 位数字验证码" :prefix-icon="Key">
              <template #append>
                <el-button :disabled="counting > 0" :loading="sending" @click="onSendCode">
                  {{ counting > 0 ? `${counting} 秒后重发` : '获取验证码' }}
                </el-button>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input v-model="form.password" type="password" show-password placeholder="至少 6 位" :prefix-icon="Lock" />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirm_password">
            <el-input v-model="form.confirm_password" type="password" show-password placeholder="请再次输入密码" :prefix-icon="Lock" />
          </el-form-item>

          <el-collapse v-model="optionalOpen" style="margin-bottom: 4px">
            <el-collapse-item name="optional">
              <template #title>
                <span style="font-size: 13px; color: var(--app-text-muted)">选填资料（用户名 / 姓名 / 手机号）</span>
              </template>
              <el-form-item label="用户名" prop="username">
                <el-input v-model="form.username" placeholder="3-50 位字母、数字或下划线，留空则自动生成" />
              </el-form-item>
              <el-form-item label="真实姓名" prop="real_name">
                <el-input v-model="form.real_name" placeholder="选填" />
              </el-form-item>
              <el-form-item label="手机号" prop="phone">
                <el-input v-model="form.phone" placeholder="选填，用于门店联系" />
              </el-form-item>
            </el-collapse-item>
          </el-collapse>

          <el-button type="primary" :loading="loading" style="width: 100%; height: 42px" @click="onSubmit">
            注 册
          </el-button>
        </el-form>

        <div style="margin-top: 16px; font-size: 13px; color: var(--app-text-muted); text-align: center">
          已有账号？<router-link to="/login" class="brand-text">返回登录</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Key, Lock, Message, Van } from '@element-plus/icons-vue'
import ThemeToggle from '../components/ThemeToggle.vue'
import { authApi } from '../api'
import { useAuthStore } from '../store/auth'

const auth = useAuthStore()
const router = useRouter()
const formRef = ref()
const loading = ref(false)
const sending = ref(false)
const counting = ref(0)
const debugCode = ref('')
const optionalOpen = ref([])

const form = reactive({
  email: '',
  code: '',
  password: '',
  confirm_password: '',
  username: '',
  real_name: '',
  phone: ''
})

const EMAIL_RE = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/
const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { pattern: EMAIL_RE, message: '邮箱格式不正确', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入邮箱验证码', trigger: 'blur' },
    { pattern: /^\d{4,8}$/, message: '验证码为 4-8 位数字', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 64, message: '密码长度 6-64 位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (rule, value, cb) => (value === form.password ? cb() : cb(new Error('两次输入的密码不一致'))),
      trigger: 'blur'
    }
  ],
  username: [{ pattern: /^[A-Za-z0-9_]{3,50}$/, message: '仅支持字母、数字、下划线，长度 3-50 位', trigger: 'blur' }],
  phone: [{ pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' }]
}

let timer = null

function startCountdown(seconds) {
  counting.value = seconds
  clearInterval(timer)
  timer = setInterval(() => {
    counting.value -= 1
    if (counting.value <= 0) {
      clearInterval(timer)
      counting.value = 0
    }
  }, 1000)
}

onBeforeUnmount(() => clearInterval(timer))

async function onSendCode() {
  try {
    await formRef.value.validateField('email')
  } catch {
    return
  }
  sending.value = true
  try {
    const data = await authApi.sendEmailCode(form.email.trim().toLowerCase(), 'register')
    if (data?.debug_code) {
      // 未配置 SMTP 时的本地调试兜底：自动回填验证码
      debugCode.value = data.debug_code
      form.code = data.debug_code
      ElMessage.warning('SMTP 未配置，已启用本地调试模式，验证码已自动填入')
    } else {
      ElMessage.success(`验证码已发送至 ${form.email}，${data?.expire_minutes ?? 5} 分钟内有效`)
    }
    startCountdown(data?.cooldown_seconds ?? 60)
  } catch {
    /* 错误提示已由 axios 拦截器统一处理 */
  } finally {
    sending.value = false
  }
}

async function onSubmit() {
  await formRef.value.validate()
  loading.value = true
  try {
    const payload = {
      email: form.email.trim().toLowerCase(),
      code: form.code.trim(),
      password: form.password,
      username: form.username.trim() || null,
      real_name: form.real_name.trim() || null,
      phone: form.phone.trim() || null
    }
    await auth.register(payload)
    ElMessage.success('注册成功，请使用邮箱登录')
    router.push('/login')
  } finally {
    loading.value = false
  }
}
</script>
