import { defineStore } from 'pinia'

const STORAGE_KEY = 'app-theme-mode'

/** 读取初始主题：优先用户选择，其次跟随系统 */
export function resolveInitialMode() {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved === 'light' || saved === 'dark') return saved
  const preferDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
  return preferDark ? 'dark' : 'light'
}

/** 将主题应用到 <html>：Element Plus 暗色依赖 html.dark */
export function applyTheme(mode) {
  const root = document.documentElement
  root.classList.toggle('dark', mode === 'dark')
  root.setAttribute('data-theme', mode)
  root.style.colorScheme = mode
}

/** 在应用挂载前调用，避免首屏闪烁 */
export function applyInitialTheme() {
  applyTheme(resolveInitialMode())
}

export const useThemeStore = defineStore('theme', {
  state: () => ({ mode: resolveInitialMode() }),
  getters: {
    isDark: (state) => state.mode === 'dark'
  },
  actions: {
    setMode(mode) {
      this.mode = mode
      localStorage.setItem(STORAGE_KEY, mode)
      applyTheme(mode)
    },
    toggle() {
      this.setMode(this.mode === 'dark' ? 'light' : 'dark')
    }
  }
})
