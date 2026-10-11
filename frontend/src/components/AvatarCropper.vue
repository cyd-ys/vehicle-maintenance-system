<template>
  <el-dialog
    :model-value="modelValue"
    title="裁剪头像"
    width="420px"
    append-to-body
    :close-on-click-modal="false"
    @update:model-value="(v) => emit('update:modelValue', v)"
    @closed="cleanup"
  >
    <div class="cropper-body">
      <div
        class="cropper-viewport"
        :class="{ dragging }"
        :style="{ width: `${VIEWPORT}px`, height: `${VIEWPORT}px` }"
        @pointerdown="onDown"
        @pointermove="onMove"
        @pointerup="onUp"
        @pointercancel="onUp"
        @pointerleave="onUp"
        @wheel.prevent="onWheel"
      >
        <img
          v-if="src"
          ref="imgRef"
          class="cropper-img"
          :src="src"
          :style="imgStyle"
          alt="待裁剪图片"
          draggable="false"
        />
        <div v-else class="cropper-loading">图片加载中…</div>
        <div class="cropper-ring"></div>
      </div>

      <div class="cropper-bar">
        <el-icon :size="16" class="cropper-ic"><ZoomOut /></el-icon>
        <el-slider
          class="cropper-zoom"
          :model-value="zoom"
          :min="1"
          :max="3"
          :step="0.01"
          :show-tooltip="false"
          @input="setZoom"
        />
        <el-icon :size="16" class="cropper-ic"><ZoomIn /></el-icon>
        <span class="cropper-zoomval">{{ zoom.toFixed(1) }}×</span>
      </div>

      <div class="field-tip">
        拖动图片调整位置，滚轮或滑杆缩放；确认后将输出 400×400 的圆形头像。
      </div>
    </div>

    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="working" @click="confirm">确认裁剪</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { ZoomIn, ZoomOut } from '@element-plus/icons-vue'
import {
  anchorZoom,
  aspectOk,
  centerOffset,
  clampOffset,
  cropParams,
  displaySize,
  fitWithin
} from '../utils/crop'

const VIEWPORT = 320 // 裁剪视口边长（CSS 像素）
const OUTPUT = 400 // 输出头像边长
const MAX_SRC = 1600 // 原图长边超过该值时先等比压缩，避免 DOM 元素过大
const MAX_INPUT = 8 * 1024 * 1024 // 原图体积上限（裁剪后必然远小于 2MB）

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  file: { type: Object, default: null }
})
const emit = defineEmits(['update:modelValue', 'confirm'])

const src = ref('')
const natural = ref({ w: 0, h: 0 })
const zoom = ref(1)
const offsetX = ref(0)
const offsetY = ref(0)
const dragging = ref(false)
const working = ref(false)
const imgRef = ref()

let dragStart = null
let objectUrl = ''

const disp = computed(() => displaySize(natural.value.w, natural.value.h, VIEWPORT, zoom.value))

const imgStyle = computed(() => ({
  width: `${disp.value.w}px`,
  height: `${disp.value.h}px`,
  transform: `translate3d(${offsetX.value}px, ${offsetY.value}px, 0)`
}))

/* ---------------- 载入待裁剪图片 ---------------- */
function readImage(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const img = new Image()
    img.onload = () => {
      URL.revokeObjectURL(url)
      resolve(img)
    }
    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('image load failed'))
    }
    img.src = url
  })
}

function cleanup() {
  if (objectUrl) {
    URL.revokeObjectURL(objectUrl)
    objectUrl = ''
  }
  src.value = ''
  natural.value = { w: 0, h: 0 }
  zoom.value = 1
  offsetX.value = 0
  offsetY.value = 0
  dragStart = null
  dragging.value = false
}

async function loadFile(file) {
  cleanup()
  try {
    const img = await readImage(file)
    if (!aspectOk(img.width, img.height)) {
      ElMessage.error('图片长宽比过于极端（超过 8:1），请换一张更接近方形的图片')
      emit('update:modelValue', false)
      return
    }
    const fit = fitWithin(img.width, img.height, MAX_SRC)
    if (fit.w === img.width && fit.h === img.height) {
      objectUrl = URL.createObjectURL(file)
      src.value = objectUrl
    } else {
      // 超大图先等比压缩，避免生成巨大的 DOM 元素
      const canvas = document.createElement('canvas')
      canvas.width = fit.w
      canvas.height = fit.h
      canvas.getContext('2d').drawImage(img, 0, 0, fit.w, fit.h)
      src.value = canvas.toDataURL('image/png')
    }
    natural.value = { w: fit.w, h: fit.h }
    zoom.value = 1
    const o = centerOffset(fit.w, fit.h, VIEWPORT, 1)
    offsetX.value = o.offsetX
    offsetY.value = o.offsetY
  } catch {
    ElMessage.error('图片读取失败，请换一张图片试试')
    emit('update:modelValue', false)
  }
}

watch(
  () => [props.modelValue, props.file],
  () => {
    const f = props.file
    if (!props.modelValue || !f) return
    if (f.size > MAX_INPUT) {
      ElMessage.error('原图不能超过 8MB')
      emit('update:modelValue', false)
      return
    }
    loadFile(f)
  },
  { immediate: true }
)

/* ---------------- 拖动 ---------------- */
function onDown(e) {
  if (!src.value) return
  dragging.value = true
  dragStart = { x: e.clientX, y: e.clientY, ox: offsetX.value, oy: offsetY.value }
  try {
    e.currentTarget.setPointerCapture(e.pointerId)
  } catch {
    /* 某些环境不支持指针捕获，忽略即可（拖动依然可用） */
  }
}

function onMove(e) {
  if (!dragging.value || !dragStart) return
  offsetX.value = clampOffset(dragStart.ox + (e.clientX - dragStart.x), disp.value.w, VIEWPORT)
  offsetY.value = clampOffset(dragStart.oy + (e.clientY - dragStart.y), disp.value.h, VIEWPORT)
}

function onUp(e) {
  if (!dragging.value) return
  dragging.value = false
  dragStart = null
  try {
    e?.currentTarget?.releasePointerCapture?.(e.pointerId)
  } catch {
    /* 未捕获时释放会抛错，忽略 */
  }
}

/* ---------------- 缩放（以视口中心为锚点） ---------------- */
function setZoom(next) {
  if (!natural.value.w) return
  const z = Math.min(3, Math.max(1, Number(next) || 1))
  const r = anchorZoom({
    imgW: natural.value.w,
    imgH: natural.value.h,
    viewport: VIEWPORT,
    fromZoom: zoom.value,
    toZoom: z,
    offsetX: offsetX.value,
    offsetY: offsetY.value
  })
  zoom.value = r.zoom
  offsetX.value = r.offsetX
  offsetY.value = r.offsetY
}

function onWheel(e) {
  setZoom(zoom.value - Math.sign(e.deltaY) * 0.08)
}

/* ---------------- 导出 ---------------- */
async function confirm() {
  if (!imgRef.value || !natural.value.w) return
  working.value = true
  try {
    const p = cropParams({
      imgW: natural.value.w,
      imgH: natural.value.h,
      viewport: VIEWPORT,
      zoom: zoom.value,
      offsetX: offsetX.value,
      offsetY: offsetY.value,
      output: OUTPUT
    })
    const canvas = document.createElement('canvas')
    canvas.width = OUTPUT
    canvas.height = OUTPUT
    const ctx = canvas.getContext('2d')
    ctx.imageSmoothingEnabled = true
    ctx.imageSmoothingQuality = 'high'
    ctx.drawImage(imgRef.value, p.dx, p.dy, p.dw, p.dh)

    const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/png', 0.95))
    if (!blob) throw new Error('toBlob failed')
    emit('confirm', new File([blob], `avatar_${Date.now()}.png`, { type: 'image/png' }))
  } catch {
    ElMessage.error('裁剪失败，请重试')
  } finally {
    working.value = false
  }
}
</script>

<style scoped>
.cropper-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
}

.cropper-viewport {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  background: #12161d;
  cursor: grab;
  touch-action: none;
  flex: none;
}

.cropper-viewport.dragging {
  cursor: grabbing;
}

.cropper-img {
  position: absolute;
  left: 0;
  top: 0;
  display: block;
  user-select: none;
  -webkit-user-drag: none;
  will-change: transform;
}

.cropper-loading {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  color: #8b95a5;
  font-size: 13px;
}

/* 圆形裁剪框：外圈用超大外阴影压暗 */
.cropper-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.92);
  box-shadow: 0 0 0 999px rgba(0, 0, 0, 0.45);
  pointer-events: none;
}

.cropper-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  max-width: 340px;
}

.cropper-zoom {
  flex: 1;
}

.cropper-ic {
  color: var(--app-text-muted);
}

.cropper-zoomval {
  width: 40px;
  text-align: right;
  font-size: 12px;
  color: var(--app-text-muted);
  font-variant-numeric: tabular-nums;
}
</style>
