import { Outlet } from 'react-router'

import PublicHeader from './PublicHeader'

// Login có header công khai; Register độc lập theo hai bản desktop đã bàn giao.
// Form, illustration và xác thực được triển khai cùng feature auth ở bước riêng.
export default function AuthLayout({ variant }: { variant: 'login' | 'register' }) {
  return (
    <div className={`auth-shell auth-shell--${variant}`}>
      <a className="skip-link" href="#main-content">Đến nội dung chính</a>
      {variant === 'login' && <PublicHeader />}
      <main id="main-content" className="auth-main" tabIndex={-1}>
        <Outlet />
      </main>
    </div>
  )
}
