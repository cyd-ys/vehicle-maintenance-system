import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 前后端分离：开发期通过代理访问 FastAPI 后端（论文 4.1）
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    open: false,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      // 用户上传的头像等静态资源由后端 /uploads 提供
      '/uploads': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})
