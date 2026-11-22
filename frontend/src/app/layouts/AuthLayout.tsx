import { Outlet } from 'react-router'

import PublicHeader from './PublicHeader'

// Login có header công khai; Register độc lập theo hai bản desktop đã bàn giao.
// Feature sở hữu form/ảnh; shell sở hữu main/header/footer để không lồng landmark.
export default function AuthLayout({ variant }: { variant: 'login' | 'register' }) {
  return (
    <div className={`auth-shell auth-shell--${variant}`}>
      <a className="skip-link" href="#main-content">Đến nội dung chính</a>
      {variant === 'login' && <PublicHeader />}
      <main id="main-content" className="auth-main" tabIndex={-1}>
        <Outlet />
      </main>
      {variant === 'login' && (
        // Chỉ dùng liên kết repository đã có; không chép thông tin liên hệ cá nhân từ ảnh Figma.
        <footer className="login-footer">
          <span>Learning English Tracker</span>
          <a href="https://github.com/Q1Patrick/Learning-English-Tracker" target="_blank" rel="noopener noreferrer">GitHub</a>
        </footer>
      )}
    </div>
  )
}
