import { Menu, X } from 'lucide-react'
import { useId, useRef, useState } from 'react'
import type { FormEvent, Ref } from 'react'
import { Link, useNavigate } from 'react-router'

import { implementedNavigationItems } from './navigation'
import LayoutIcon from './LayoutIcon'
import { isSameTabNavigation } from './navigationEvents'

interface HeaderProps {
  isMenuOpen: boolean
  onMenuToggle: () => void
  onNavigate: () => void
  menuButtonRef?: Ref<HTMLButtonElement>
}

function normalizeSearch(value: string) {
  return value
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .replace(/đ/gi, 'd')
    .toLowerCase()
    .trim()
}

export default function Header({
  isMenuOpen,
  onMenuToggle,
  onNavigate,
  menuButtonRef,
}: HeaderProps) {
  const [query, setQuery] = useState('')
  const [isSearchOpen, setIsSearchOpen] = useState(false)
  const searchInputRef = useRef<HTMLInputElement>(null)
  const searchId = useId()
  const resultsId = `${searchId}-results`
  const navigate = useNavigate()
  const normalizedQuery = normalizeSearch(query)
  const matches = normalizedQuery
    ? implementedNavigationItems.filter((item) =>
        normalizeSearch(`${item.label} ${item.keywords ?? ''}`).includes(normalizedQuery),
      )
    : []
  const showResults = isSearchOpen && Boolean(normalizedQuery)

  function finishNavigation() {
    setQuery('')
    setIsSearchOpen(false)
    onNavigate()
  }

  function handleSearchSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    // Enter chỉ chuyển khi có đúng một kết quả; nhiều kết quả chọn bằng Link.
    if (matches.length === 1) {
      navigate(matches[0].to)
      finishNavigation()
    } else {
      setIsSearchOpen(true)
    }
  }

  return (
    <header className="app-header">
      <button
        ref={menuButtonRef}
        type="button"
        className="app-header__icon-button app-header__menu-button"
        aria-label={isMenuOpen ? 'Đóng menu điều hướng' : 'Mở menu điều hướng'}
        aria-controls="app-sidebar"
        aria-expanded={isMenuOpen}
        onClick={onMenuToggle}
      >
        {isMenuOpen ? <X size={22} aria-hidden="true" /> : <Menu size={22} aria-hidden="true" />}
      </button>

      {/* Chỉ tìm các trang đã có; không mô phỏng tìm kiếm dữ liệu hoặc gọi API. */}
      <form
        className="app-header__search"
        role="search"
        aria-label="Tìm trang trong ứng dụng"
        onSubmit={handleSearchSubmit}
        onBlur={(event) => {
          if (!event.currentTarget.contains(event.relatedTarget)) {
            setIsSearchOpen(false)
          }
        }}
        onKeyDown={(event) => {
          if (event.key === 'Escape' && showResults) {
            event.preventDefault()
            event.stopPropagation()
            setQuery('')
            setIsSearchOpen(false)
            searchInputRef.current?.focus()
          }
        }}
      >
        <LayoutIcon name="search" className="app-header__search-icon" />
        <label className="visually-hidden" htmlFor={searchId}>
          Tìm trang
        </label>
        <input
          ref={searchInputRef}
          id={searchId}
          className="app-header__search-input"
          type="search"
          placeholder="Tìm trang…"
          autoComplete="off"
          value={query}
          aria-controls={showResults ? resultsId : undefined}
          onChange={(event) => {
            setQuery(event.target.value)
            setIsSearchOpen(true)
          }}
          onFocus={() => setIsSearchOpen(true)}
        />
        {showResults && (
          <div id={resultsId} className="app-header__search-results">
            <p role="status">
              {matches.length ? `${matches.length} trang phù hợp` : 'Không tìm thấy trang phù hợp.'}
            </p>
            {matches.length > 0 && (
              <ul aria-label="Kết quả tìm trang">
                {matches.map(({ id, label, to, icon: Icon }) => (
                  <li key={id}>
                    <Link
                      to={to}
                      onClick={(event) => {
                        if (isSameTabNavigation(event)) finishNavigation()
                      }}
                    >
                      <Icon size={18} aria-hidden="true" />
                      <span>{label}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </form>

      <div className="app-header__actions">
        {/* Chưa có API thông báo; không gắn badge số lượng hoặc thao tác giả. */}
        <button
          type="button"
          className="app-header__icon-button"
          disabled
          aria-label="Thông báo — Sắp có"
          title="Thông báo — Sắp có"
        >
          <LayoutIcon name="notification" />
          <span className="app-header__coming-soon">Sắp có</span>
        </button>
        <Link
          className="app-header__profile"
          to="/profile"
          onClick={(event) => {
            if (isSameTabNavigation(event)) onNavigate()
          }}
        >
          <span className="app-header__avatar" aria-hidden="true">
            <LayoutIcon name="user" />
          </span>
          <span>Hồ sơ</span>
        </Link>
      </div>
    </header>
  )
}
