<template>
  <div class="plate-input">
    <div class="plate-input-row">
      <el-select
        v-model="province"
        class="plate-province"
        placeholder="省份"
        filterable
        :teleported="true"
      >
        <el-option v-for="p in PROVINCES" :key="p.code" :label="p.code" :value="p.code">
          <span>{{ p.code }}</span>
          <span style="float: right; color: var(--app-text-muted); font-size: 12px">{{ p.name }}</span>
        </el-option>
      </el-select>

      <el-input
        v-model="rest"
        class="plate-rest"
        :maxlength="7"
        placeholder="字母 + 数字，如 A12345 / AD12345"
        @input="onInput"
      />
    </div>

    <div class="plate-hint" :class="status.ok ? 'ok' : 'warn'">
      <el-icon v-if="!full"><InfoFilled /></el-icon>
      <el-icon v-else-if="status.ok"><CircleCheckFilled /></el-icon>
      <el-icon v-else><WarningFilled /></el-icon>
      <span>{{ hintText }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { InfoFilled, CircleCheckFilled, WarningFilled } from '@element-plus/icons-vue'
import { PROVINCES, sanitizePlateRest, validatePlate } from '../utils/plate'

const props = defineProps({
  modelValue: { type: String, default: '' }
})
const emit = defineEmits(['update:modelValue', 'change'])

const province = ref('')
const rest = ref('')

const full = computed(() => (province.value ? province.value + rest.value : rest.value))
const status = computed(() => validatePlate(full.value))

const hintText = computed(() => {
  if (!full.value) {
    return '先选省份简称，再输入字母和数字；新能源车牌为 8 位（如 琼BD12345）'
  }
  return status.value.ok ? `格式正确 · ${status.value.message}` : status.value.message
})

function initWith(value) {
  const s = (value || '').toUpperCase()
  if (s && PROVINCES.some((p) => p.code === s[0])) {
    province.value = s[0]
    rest.value = sanitizePlateRest(s.slice(1))
  } else {
    province.value = ''
    rest.value = sanitizePlateRest(s)
  }
}

// 外部值变化时同步（编辑车辆场景）
watch(
  () => props.modelValue,
  (v) => {
    if (full.value !== (v || '').toUpperCase()) initWith(v)
  },
  { immediate: true }
)

// 内部变化时向上同步
watch([province, rest], () => {
  const value = full.value
  if (value !== (props.modelValue || '').toUpperCase()) {
    emit('update:modelValue', value)
    emit('change', value)
  }
})

function onInput(val) {
  const clean = sanitizePlateRest(val)
  if (clean !== val) rest.value = clean
}
</script>

<style scoped>
.plate-input-row {
  display: flex;
  gap: 8px;
  width: 100%;
}
.plate-province {
  width: 104px;
  flex: none;
}
.plate-rest {
  flex: 1;
}
.plate-hint {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  line-height: 1.5;
  margin-top: 5px;
}
.plate-hint.warn {
  color: var(--app-text-muted);
}
.plate-hint.ok {
  color: #52c41a;
}
</style>
