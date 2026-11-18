import { useEffect, useRef } from 'react'
import { useLocation } from 'react-router'

import AppRouter from './app/AppRouter'
import { getPageTitle } from './app/pageTitles'
import './app/layouts/layouts.css'

// Mỗi layout sở hữu một vùng main; không bọc thêm main ở đây để tránh landmark lồng nhau.
export default function App() {
  const { pathname } = useLocation()
  const previousPath = useRef(pathname)

  useEffect(() => {
    // Query/hash không đổi trang: giữ title và focus khi người dùng đang lọc dữ liệu.
    document.title = getPageTitle(pathname)
  }, [pathname])

  useEffect(() => {
    if (previousPath.current !== pathname) {
      // Đợi trang mới mount rồi chuyển focus; link cũ có thể đã bị tháo cùng layout.
      document.getElementById('main-content')?.focus({ preventScroll: true })
      previousPath.current = pathname
    }
  }, [pathname])

  return <AppRouter />
}
