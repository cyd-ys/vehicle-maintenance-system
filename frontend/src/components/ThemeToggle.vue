<template>
  <el-tooltip :content="isDark ? '切换到浅色模式' : '切换到暗色模式'" placement="bottom" :show-after="200">
    <el-switch
      v-model="dark"
      class="theme-switch"
      inline-prompt
      :active-icon="Moon"
      :inactive-icon="Sunny"
      :width="46"
    />
  </el-tooltip>
</template>

<script setup>
import { computed } from 'vue'
import { Moon, Sunny } from '@element-plus/icons-vue'
import { useThemeStore } from '../store/theme'

const theme = useThemeStore()
const isDark = computed(() => theme.isDark)
const dark = computed({
  get: () => theme.isDark,
  set: (val) => theme.setMode(val ? 'dark' : 'light')
})
</script>

<style scoped>
.theme-switch {
  --el-switch-on-color: #3a4a63;
  --el-switch-off-color: #c6d4ea;
}
</style>
