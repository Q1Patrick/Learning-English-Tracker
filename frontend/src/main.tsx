import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router'

import App from './App.tsx'
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
      <App />
    </BrowserRouter>
  </StrictMode>,
)
