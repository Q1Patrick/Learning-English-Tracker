import { Link, NavLink } from 'react-router'

import logo from '../../assets/layout/logo.svg'
import LayoutIcon from './LayoutIcon'
import { accountNavigationItems, navigationItems } from './navigation'
import type { AppNavigationItem } from './navigation'
import { isSameTabNavigation } from './navigationEvents'

interface SidebarProps {
  isOpen: boolean
  onNavigate: () => void
}

function NavigationItem({ item, onNavigate }: { item: AppNavigationItem; onNavigate: () => void }) {
  const content = (
    <>
      <LayoutIcon name={item.id} className="app-sidebar__icon" />
      <span>{item.label}</span>
    </>
  )

  // Mục chưa có route không nhận focus/click; không tạo URL giả.
  if (item.disabled || !item.to) {
    return (
      <span className="app-sidebar__link" role="link" aria-disabled="true">
        {content}
        <small>Sắp có</small>
      </span>
    )
  }

  return (
    <NavLink
      to={item.to}
      end={item.end}
      className={({ isActive }) => `app-sidebar__link${isActive ? ' active' : ''}`}
      onClick={(event) => {
        if (isSameTabNavigation(event)) onNavigate()
      }}
    >
      {content}
    </NavLink>
  )
}

export default function Sidebar({ isOpen, onNavigate }: SidebarProps) {
  return (
    <aside id="app-sidebar" className={`app-sidebar${isOpen ? ' is-open' : ''}`} aria-label="Thanh bên">
      <Link
        className="app-sidebar__brand"
        to="/"
        onClick={(event) => {
          if (isSameTabNavigation(event)) onNavigate()
        }}
      >
        <img src={logo} width={48} height={48} alt="" />
        <strong>Learning English<br />Tracker</strong>
      </Link>
      <nav className="app-sidebar__nav" aria-label="Điều hướng ứng dụng">
        {navigationItems.map((item) => <NavigationItem key={item.id} item={item} onNavigate={onNavigate} />)}
        <div className="app-sidebar__section" role="group" aria-label="Tài khoản">
          {accountNavigationItems.map((item) => <NavigationItem key={item.id} item={item} onNavigate={onNavigate} />)}
        </div>
      </nav>
    </aside>
  )
}
