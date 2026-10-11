<template>
  <span
    class="ua"
    :style="{ width: `${size}px`, height: `${size}px`, fontSize: `${Math.round(size * 0.42)}px` }"
  >
    <img v-if="src" :src="src" alt="头像" />
    <template v-else>{{ text }}</template>
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  user: { type: Object, default: null },
  size: { type: Number, default: 26 }
})

// 头像地址（后端返回相对路径 /uploads/avatars/xxx.png，开发期由 Vite 代理转发）
const src = computed(() => props.user?.avatar || '')
// 无头像时退化为姓名首字母
const text = computed(() => (props.user?.real_name || props.user?.username || 'U').slice(0, 1).toUpperCase())
</script>

<style scoped>
.ua {
  display: inline-grid;
  place-items: center;
  flex: none;
  border-radius: 50%;
  overflow: hidden;
  color: #fff;
  font-weight: 700;
  line-height: 1;
  background: linear-gradient(135deg, var(--brand) 0%, var(--brand-2) 130%);
  user-select: none;
}

.ua img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}
</style>
