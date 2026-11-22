import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router'

import App from './App.tsx'
import AuthProvider from './features/auth/AuthProvider'
import './index.css'

const rootElement = document.getElementById('root')

// Báo lỗi rõ vị trí khi HTML deploy thiếu điểm mount, thay vì chỉ hiện trang trắng.
if (!rootElement) {
  throw new Error('Không tìm thấy #root. Kiểm tra frontend/index.html trước khi khởi động React.')
}

createRoot(rootElement).render(
  <StrictMode>
    {/* Chỉ đặt một BrowserRouter tại entry point; AppRouter chỉ khai báo các route. */}
    <BrowserRouter>
      {/* Một nguồn AuthState chung cho tất cả route; không khởi tạo lại Provider khi chuyển trang. */}
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
