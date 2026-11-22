import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router'

import { isAbortError } from '../../shared/api/errors'
import { useAuth } from './useAuth'
import './session-status.css'

// Component tài khoản đọc AuthState thật. Nó không thay cho route guard của FE-03.6.
export default function SessionStatus() {
  const auth = useAuth()
  const [isSigningOut, setIsSigningOut] = useState(false)
  const [error, setError] = useState('')
  const request = useRef<AbortController | null>(null)
  const navigate = useNavigate()

  useEffect(() => () => { request.current?.abort(); request.current = null }, [])

  async function handleSignOut() {
    if (request.current) return
    const controller = new AbortController()
    request.current = controller
    setIsSigningOut(true)
    setError('')
    try {
      // Chỉ báo thành công khi backend đã hủy session; không chỉ xóa state ở React.
      await auth.signOut({ signal: controller.signal })
      if (!controller.signal.aborted) navigate('/login', { replace: true })
    } catch (failure: unknown) {
      if (!controller.signal.aborted && !isAbortError(failure)) {
        setError('Chưa xác nhận được đăng xuất. Vui lòng kiểm tra kết nối và thử lại.')
      }
    } finally {
      if (request.current === controller) {
        request.current = null
        if (!controller.signal.aborted) setIsSigningOut(false)
      }
    }
  }

  return (
    <div className="session-status" role="region" aria-label="Phiên đăng nhập" data-auth-status={auth.status}>
      {auth.status === 'checking' && <p role="status">Đang kiểm tra phiên đăng nhập…</p>}
      {auth.status === 'authenticated' && auth.user && (
        <>
          <p>Đã đăng nhập: <strong>{auth.user.email}</strong></p>
          <button type="button" onClick={handleSignOut} disabled={isSigningOut}>
            {isSigningOut ? 'Đang đăng xuất…' : 'Đăng xuất'}
          </button>
        </>
      )}
      {auth.status === 'anonymous' && <p>Bạn chưa đăng nhập. <Link to="/login">Đăng nhập</Link></p>}
      {auth.status === 'unavailable' && (
        <>
          <p role="alert">Chưa thể kiểm tra phiên. Vui lòng kiểm tra kết nối.</p>
          <button type="button" onClick={() => { void auth.retrySession().catch(() => {}) }}>Thử lại</button>
        </>
      )}
      {error && <p className="session-status__error" role="alert">{error}</p>}
    </div>
  )
}
