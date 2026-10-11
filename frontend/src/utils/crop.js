/**
 * 头像裁剪的纯计算函数（不依赖 DOM，便于单独测试）。
 *
 * 坐标约定：
 *   - viewport 是正方形裁剪视口的边长（CSS 像素）
 *   - 图片按「cover」方式铺满视口，再乘以 zoom（1~3 倍）
 *   - offsetX / offsetY 是图片左上角相对视口左上角的偏移，恒 <= 0（保证覆盖视口）
 */

export const clamp = (v, min, max) => Math.min(max, Math.max(min, v))

/** cover 基础缩放：让图片刚好铺满正方形视口 */
export function coverScale(imgW, imgH, viewport) {
  return Math.max(viewport / imgW, viewport / imgH)
}

/** 当前 zoom 下图片的显示尺寸 */
export function displaySize(imgW, imgH, viewport, zoom) {
  const s = coverScale(imgW, imgH, viewport) * zoom
  return { w: imgW * s, h: imgH * s }
}

/**
 * 约束偏移：图片必须始终覆盖视口，即 offset ∈ [viewport - displayLen, 0]。
 * 若图片比视口还小（理论不会发生），则居中。
 */
export function clampOffset(offset, displayLen, viewport) {
  const min = viewport - displayLen
  if (min >= 0) return min / 2
  return clamp(offset, min, 0)
}

/** 初始居中偏移 */
export function centerOffset(imgW, imgH, viewport, zoom = 1) {
  const { w, h } = displaySize(imgW, imgH, viewport, zoom)
  return { offsetX: (viewport - w) / 2, offsetY: (viewport - h) / 2 }
}

/**
 * 以视口中心为锚点缩放：保证缩放前后「视口中心对应的图片位置」不变。
 * 因为显示尺寸与 zoom 成正比，所以尺度比就等于 zoom 比。
 */
export function anchorZoom({ imgW, imgH, viewport, fromZoom, toZoom, offsetX, offsetY }) {
  const ratio = toZoom / fromZoom
  const cx = viewport / 2
  const cy = viewport / 2
  let nx = cx - (cx - offsetX) * ratio
  let ny = cy - (cy - offsetY) * ratio
  const { w, h } = displaySize(imgW, imgH, viewport, toZoom)
  nx = clampOffset(nx, w, viewport)
  ny = clampOffset(ny, h, viewport)
  return { zoom: toZoom, offsetX: nx, offsetY: ny }
}

/**
 * 把「视口坐标系」映射到「输出画布坐标系」。
 * 视口边长 viewport 对应输出边长 output，比例为 k。
 */
export function cropParams({ imgW, imgH, viewport, zoom, offsetX, offsetY, output }) {
  const k = output / viewport
  const { w, h } = displaySize(imgW, imgH, viewport, zoom)
  return { dx: offsetX * k, dy: offsetY * k, dw: w * k, dh: h * k }
}

/** 长宽比是否在可接受范围（避免出现极端的超宽/超高图） */
export function aspectOk(imgW, imgH, limit = 8) {
  if (!imgW || !imgH) return false
  const r = imgW / imgH
  return r <= limit && r >= 1 / limit
}

/** 把长边压到 max 以内，返回等比缩放后的尺寸（不放大） */
export function fitWithin(imgW, imgH, max) {
  const s = Math.min(1, max / Math.max(imgW, imgH))
  return { w: Math.round(imgW * s), h: Math.round(imgH * s) }
}
