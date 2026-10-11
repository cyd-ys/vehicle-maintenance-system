<template>
  <div>
    <!-- 头像设置 -->
    <el-card shadow="never" class="mb-12">
      <template #header><b>头像</b></template>
      <div class="avatar-row">
        <div class="avatar-preview">
          <img v-if="auth.user?.avatar" :src="auth.user.avatar" alt="头像" />
          <span v-else class="avatar-fallback">{{ avatarText }}</span>
        </div>
        <div class="avatar-actions">
          <div style="display: flex; gap: 10px; flex-wrap: wrap">
            <el-button type="primary" :loading="uploading" @click="pickFile">上传新头像</el-button>
            <el-button :disabled="!auth.user?.avatar || uploading" @click="doResetAvatar">恢复默认</el-button>
            <input
              ref="fileInput"
              type="file"
              accept="image/jpeg,image/png,image/webp,image/gif"
              hidden
              @change="onFileChange"
            />
          </div>
          <div class="field-tip">
            支持 JPG / PNG / WebP / GIF，原图不超过 8MB；上传前可拖动、缩放裁剪，输出 400×400 圆形头像。
          </div>
        </div>
      </div>
    </el-card>

    <AvatarCropper v-model="cropVisible" :file="cropFile" @confirm="onCropped" />

    <el-row :gutter="16">
      <el-col :xs="24" :lg="13">
        <el-card shadow="never" class="mb-12">
          <template #header><b>基本资料</b></template>
          <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="form.username" placeholder="3-50 位字母、数字或下划线">
                <template #prefix><el-icon><User /></el-icon></template>
              </el-input>
              <div class="field-tip">用户名同时是登录账号之一，修改后请使用新用户名登录</div>
            </el-form-item>
            <el-form-item label="绑定邮箱">
              <div style="display: flex; gap: 8px; width: 100%">
                <el-input :value="auth.user?.email || '未绑定'" disabled style="flex: 1">
                  <template #prefix><el-icon><Message /></el-icon></template>
                </el-input>
                <el-button @click="openEmailDialog">更换邮箱</el-button>
              </div>
              <div class="field-tip">邮箱用于找回密码，更换需通过新邮箱验证码校验</div>
            </el-form-item>
            <el-form-item label="角色">
              <el-tag>{{ auth.roleText }}</el-tag>
              <span v-if="auth.user?.store_id" class="text-muted" style="margin-left: 10px">
                所属门店 ID：{{ auth.user.store_id }}
              </span>
            </el-form-item>
            <el-form-item label="真实姓名" prop="real_name">
              <el-input v-model="form.real_name" placeholder="选填" />
            </el-form-item>
            <el-form-item label="手机号" prop="phone">
              <el-input v-model="form.phone" placeholder="选填" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="saving" @click="saveProfile">保存资料</el-button>
              <el-button @click="resetForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="11">
        <el-card shadow="never">
          <template #header><b>修改密码</b></template>
          <el-form ref="pwdRef" :model="pwd" :rules="pwdRules" label-width="90px">
            <el-form-item label="原密码" prop="old_password">
              <el-input v-model="pwd.old_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input v-model="pwd.new_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirm">
              <el-input v-model="pwd.confirm" type="password" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="changing" @click="changePwd">修改密码</el-button>
            </el-form-item>
          </el-form>
          <el-alert
            type="info"
            :closable="false"
            show-icon
            title="忘记原密码？"
            description="退出登录后，在登录页点击「忘记密码」，用绑定邮箱的验证码即可重置。"
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- 更换绑定邮箱 -->
    <el-dialog v-model="emailVisible" title="更换绑定邮箱" width="460px" append-to-body>
      <el-alert
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 14px"
        :title="`当前绑定：${auth.user?.email || '未绑定'}`"
        description="验证码将发送到「新邮箱」，验证通过后新邮箱立即生效。"
      />
      <el-alert
        v-if="emailDebugCode"
        type="warning"
        :closable="false"
        show-icon
        style="margin-bottom: 14px"
        title="当前为本地调试模式"
        :description="`未配置 SMTP，验证码已自动填入：${emailDebugCode}`"
      />
      <el-form ref="emailRef" :model="emailForm" :rules="emailRules" label-position="top">
        <el-form-item label="新邮箱" prop="email">
          <el-input v-model="emailForm.email" placeholder="请输入要绑定的新邮箱" :prefix-icon="Message" />
        </el-form-item>
        <el-form-item label="新邮箱验证码" prop="code">
          <el-input v-model="emailForm.code" maxlength="6" placeholder="6 位数字验证码" :prefix-icon="Key">
            <template #append>
              <el-button :disabled="counting > 0" :loading="sendingCode" @click="onSendChangeCode">
                {{ counting > 0 ? `${counting} 秒后重发` : '获取验证码' }}
              </el-button>
            </template>
          </el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="emailVisible = false">取消</el-button>
        <el-button type="primary" :loading="changingEmail" @click="submitEmail">确认更换</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Key, Message, User } from '@element-plus/icons-vue'
import { useAuthStore } from '../store/auth'
import { authApi } from '../api'
import AvatarCropper from './AvatarCropper.vue'

const auth = useAuthStore()

/* ---------------- 头像 ---------------- */
const uploading = ref(false)
const avatarText = computed(() =>
  (auth.user?.real_name || auth.user?.username || 'U').slice(0, 1).toUpperCase()
)

// 选图 → 裁剪 → 上传
const fileInput = ref()
const cropVisible = ref(false)
const cropFile = ref(null)

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
const MAX_PICK = 8 * 1024 * 1024 // 原图上限，裁剪后一定远小于后端 2MB 限制

function pickFile() {
  if (!fileInput.value) return
  fileInput.value.value = '' // 允许连续选择同一张图
  fileInput.value.click()
}

function onFileChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  if (!ALLOWED_TYPES.includes(file.type)) {
    ElMessage.error('仅支持 JPG / PNG / WebP / GIF 格式的图片')
    return
  }
  if (file.size > MAX_PICK) {
    ElMessage.error('原图不能超过 8MB')
    return
  }
  cropFile.value = file
  cropVisible.value = true
}

async function onCropped(file) {
  cropVisible.value = false
  await doUploadAvatar({ file })
}

async function doUploadAvatar({ file }) {
  uploading.value = true
  try {
    await authApi.uploadAvatar(file)
    await auth.fetchMe()
    ElMessage.success('头像已更新')
  } catch {
    /* 错误提示已由 axios 拦截器统一处理 */
  } finally {
    uploading.value = false
    cropFile.value = null
  }
}

async function doResetAvatar() {
  uploading.value = true
  try {
    await authApi.resetAvatar()
    await auth.fetchMe()
    ElMessage.success('已恢复默认头像')
  } catch {
    /* 错误提示已由 axios 拦截器统一处理 */
  } finally {
    uploading.value = false
  }
}

/* ---------------- 基本资料 ---------------- */
const formRef = ref()
const saving = ref(false)
const form = reactive({ username: '', real_name: '', phone: '' })

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { pattern: /^[A-Za-z0-9_]{3,50}$/, message: '仅支持字母、数字、下划线，长度 3-50 位', trigger: 'blur' }
  ],
  phone: [{ pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' }]
}

function fillForm() {
  form.username = auth.user?.username || ''
  form.real_name = auth.user?.real_name || ''
  form.phone = auth.user?.phone || ''
}

function resetForm() {
  fillForm()
  formRef.value?.clearValidate()
}

async function saveProfile() {
  await formRef.value.validate()
  saving.value = true
  try {
    await authApi.updateProfile({ ...form })
    await auth.fetchMe()
    fillForm()
    ElMessage.success('资料已更新')
  } finally {
    saving.value = false
  }
}

/* ---------------- 修改密码 ---------------- */
const pwdRef = ref()
const changing = ref(false)
const pwd = reactive({ old_password: '', new_password: '', confirm: '' })
const pwdRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [{ required: true, min: 6, max: 64, message: '新密码长度 6-64 位', trigger: 'blur' }],
  confirm: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule, value, cb) => (value === pwd.new_password ? cb() : cb(new Error('两次输入的密码不一致'))),
      trigger: 'blur'
    }
  ]
}

async function changePwd() {
  await pwdRef.value.validate()
  changing.value = true
  try {
    await authApi.changePassword({ old_password: pwd.old_password, new_password: pwd.new_password })
    ElMessage.success('密码修改成功，请重新登录')
    pwd.old_password = pwd.new_password = pwd.confirm = ''
    pwdRef.value.clearValidate()
  } finally {
    changing.value = false
  }
}

/* ---------------- 更换绑定邮箱 ---------------- */
const emailVisible = ref(false)
const emailRef = ref()
const sendingCode = ref(false)
const changingEmail = ref(false)
const counting = ref(0)
const emailDebugCode = ref('')
const emailForm = reactive({ email: '', code: '' })

const EMAIL_RE = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/
const emailRules = {
  email: [
    { required: true, message: '请输入新邮箱', trigger: 'blur' },
    { pattern: EMAIL_RE, message: '邮箱格式不正确', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入新邮箱收到的验证码', trigger: 'blur' },
    { pattern: /^\d{4,8}$/, message: '验证码为 4-8 位数字', trigger: 'blur' }
  ]
}

let timer = null
onBeforeUnmount(() => clearInterval(timer))

function openEmailDialog() {
  emailForm.email = ''
  emailForm.code = ''
  emailDebugCode.value = ''
  emailVisible.value = true
}

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

async function onSendChangeCode() {
  try {
    await emailRef.value.validateField('email')
  } catch {
    return
  }
  sendingCode.value = true
  try {
    const data = await authApi.sendChangeEmailCode(emailForm.email.trim().toLowerCase())
    if (data?.debug_code) {
      emailDebugCode.value = data.debug_code
      emailForm.code = data.debug_code
      ElMessage.warning('SMTP 未配置，已启用本地调试模式，验证码已自动填入')
    } else {
      ElMessage.success(`验证码已发送至 ${emailForm.email}，${data?.expire_minutes ?? 5} 分钟内有效`)
    }
    startCountdown(data?.cooldown_seconds ?? 60)
  } catch {
    /* 错误提示已由 axios 拦截器统一处理 */
  } finally {
    sendingCode.value = false
  }
}

async function submitEmail() {
  await emailRef.value.validate()
  changingEmail.value = true
  try {
    await authApi.changeEmail({ email: emailForm.email.trim().toLowerCase(), code: emailForm.code.trim() })
    await auth.fetchMe()
    ElMessage.success('邮箱更换成功')
    emailVisible.value = false
  } finally {
    changingEmail.value = false
  }
}

onMounted(async () => {
  await auth.fetchMe().catch(() => {})
  fillForm()
})
</script>

<style scoped>
.field-tip {
  margin-top: 4px;
  font-size: 12px;
  line-height: 1.5;
  color: var(--app-text-muted);
}

.avatar-row {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.avatar-preview {
  width: 76px;
  height: 76px;
  flex: none;
  border-radius: 50%;
  overflow: hidden;
  display: grid;
  place-items: center;
  border: 1px solid var(--app-border);
  background: var(--app-surface-2);
}

.avatar-preview img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}

.avatar-fallback {
  font-size: 30px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, var(--brand) 0%, var(--brand-2) 130%);
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
}

.avatar-actions {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
</style>
