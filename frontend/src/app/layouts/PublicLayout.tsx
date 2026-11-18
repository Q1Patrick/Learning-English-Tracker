import { Outlet } from 'react-router'

import PublicHeader from './PublicHeader'

export default function PublicLayout() {
  return (
    <div className="public-shell">
      <a className="skip-link" href="#main-content">Đến nội dung chính</a>
      <PublicHeader />
      <main id="main-content" className="public-main" tabIndex={-1}>
        <Outlet />
      </main>
    </div>
  )
}
