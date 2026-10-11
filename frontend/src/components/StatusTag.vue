<template>
  <el-tag :type="cfg.type" effect="light" size="small">{{ cfg.text }}</el-tag>
</template>

<script setup>
import { computed } from 'vue'
import { ORDER_STATUS } from '../utils/format'

const props = defineProps({
  status: { type: String, required: true }
})

const cfg = computed(() => ORDER_STATUS[props.status] || { text: props.status, type: 'info' })
</script>
