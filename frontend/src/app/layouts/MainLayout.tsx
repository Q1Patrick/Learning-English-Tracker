import { useEffect, useRef, useState } from 'react'
import { Outlet, useLocation } from 'react-router'

import Header from './Header'
import Sidebar from './Sidebar'
import SessionStatus from '../../features/auth/SessionStatus'

// Layout chỉ tổ chức giao diện. Bảo vệ các trang bằng phiên thật thuộc phần auth.
export default function MainLayout() {
  const { pathname } = useLocation()
  const [previousPath, setPreviousPath] = useState(pathname)
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const menuButtonRef = useRef<HTMLButtonElement>(null)
  const mainRef = useRef<HTMLElement>(null)

  // Back/Forward không chạy callback click Link. Chỉ điều chỉnh khi route đổi:
  // React render lại component này trước khi commit children, nên không nháy menu cũ.
  // Cập nhật previousPath cùng lúc bảo đảm điều kiện dừng, không tạo vòng render.
  if (previousPath !== pathname) {
    setPreviousPath(pathname)
    setIsMenuOpen(false)
  }

  useEffect(() => {
    if (isMenuOpen) {
      // Menu là disclosure, không phải modal; đưa focus tới link khi mở bằng bàn phím.
      const sidebar = document.getElementById('app-sidebar')
      const firstLink = sidebar?.querySelector<HTMLAnchorElement>('a[aria-current="page"]')
        ?? sidebar?.querySelector<HTMLAnchorElement>('a[href]')
      firstLink?.focus()
    }
  }, [isMenuOpen])

  function handleNavigate() {
    setIsMenuOpen(false)
    mainRef.current?.focus()
  }

  return (
    <div
      className="app-shell"
      onKeyDown={(event) => {
        if (event.key === 'Escape' && isMenuOpen) {
          event.preventDefault()
          setIsMenuOpen(false)
          // Khi resize lên desktop, nút menu có thể đã ẩn; giữ focus đang hợp lệ.
          const menuButton = menuButtonRef.current
          if (menuButton?.getClientRects().length) menuButton.focus()
        }
      }}
    >
      <a className="skip-link" href="#main-content">
        Đến nội dung chính
      </a>
      <Sidebar isOpen={isMenuOpen} onNavigate={handleNavigate} />
      <div className="app-shell__body">
        <Header
          isMenuOpen={isMenuOpen}
          onMenuToggle={() => setIsMenuOpen((open) => !open)}
          onNavigate={handleNavigate}
          menuButtonRef={menuButtonRef}
        />
        <main ref={mainRef} id="main-content" className="app-main" tabIndex={-1}>
          <SessionStatus />
          <Outlet />
        </main>
      </div>
    </div>
  )
}
