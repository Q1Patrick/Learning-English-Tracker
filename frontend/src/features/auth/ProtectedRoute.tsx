import { useEffect, useRef, useState } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router'

import type { SessionUser } from './types'
import { useAuth } from './useAuth'
import './session-status.css'

type SignOutStatus = 'idle' | 'pending' | 'failed' | 'confirmed'

export interface ProtectedRouteContext {
  user: SessionUser
  signOutStatus: SignOutStatus
  signOut: () => Promise<void>
}

export default function ProtectedRoute() {
  const auth = useAuth()
  const { pathname, search, hash } = useLocation()
  const feedbackRef = useRef<HTMLElement>(null)
  const isSigningOut = useRef(false)
  const [signOutStatus, setSignOutStatus] = useState<SignOutStatus>('idle')

  useEffect(() => {
    if (auth.status === 'unavailable') feedbackRef.current?.focus()
  }, [auth.status])

  async function signOut() {
    if (isSigningOut.current) return
    isSigningOut.current = true
    setSignOutStatus('pending')
    try {
      // Guard vẫn tồn tại khi AuthState chuyển sang checking và tháo MainLayout.
      await auth.signOut()
      setSignOutStatus('confirmed')
    } catch {
      setSignOutStatus('failed')
    } finally {
      isSigningOut.current = false
    }
  }

  if (auth.status === 'authenticated') {
    const context: ProtectedRouteContext = { user: auth.user, signOutStatus, signOut }
    return <Outlet context={context} />
  }

  if (auth.status === 'anonymous') {
    // Logout chủ động về Login chuẩn; mở trang học khi chưa có phiên thì giữ URL đích.
    if (signOutStatus === 'pending' || signOutStatus === 'confirmed') return <Navigate to="/login" replace />
    return <Navigate to="/login" replace state={{ returnTo: { pathname, search, hash } }} />
  }

  return (
    <main ref={feedbackRef} className="protected-route-status" tabIndex={-1} aria-labelledby="session-check-title">
      <h1 id="session-check-title">Phiên đăng nhập</h1>
      {auth.status === 'checking' ? (
        <p role="status">{signOutStatus === 'pending' ? 'Đang đăng xuất…' : 'Đang kiểm tra phiên đăng nhập…'}</p>
      ) : (
        <>
          <p role="alert">Chưa thể kiểm tra phiên. Vui lòng kiểm tra kết nối.</p>
          <button type="button" onClick={() => {
            feedbackRef.current?.focus()
            void auth.retrySession()
          }}>Thử lại</button>
        </>
      )}
    </main>
  )
}
