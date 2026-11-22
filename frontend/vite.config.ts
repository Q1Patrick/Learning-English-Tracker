import { fileURLToPath } from 'node:url'
import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  // Đọc cấu hình tại frontend dù npm được gọi từ thư mục gốc project.
  // DEV_* chỉ dùng ở Vite server; không đưa địa chỉ nội bộ/secret vào bundle.
  const env = loadEnv(mode, fileURLToPath(new URL('.', import.meta.url)), 'DEV_API_')
  let target: URL

  try {
    target = new URL(env.DEV_API_TARGET || 'http://127.0.0.1:8000')
  } catch {
    throw new Error('DEV_API_TARGET phải là HTTP(S) origin, ví dụ http://127.0.0.1:8000.')
  }

  if (!['http:', 'https:'].includes(target.protocol)
    || target.username || target.password || target.search || target.hash
    || target.pathname !== '/') {
    throw new Error('DEV_API_TARGET chỉ nhận HTTP(S) origin, không có credentials, path hoặc query.')
  }

  return {
    plugins: [react()],
    server: {
      proxy: {
        // Giữ nguyên /api/v1/... vì Django đã đăng ký prefix này; không rewrite.
        // Vite preview kế thừa proxy này; hosting production phải cấu hình riêng.
        '^/api(?:/|$)': { target: target.origin, changeOrigin: true },
      },
    },
  }
})
