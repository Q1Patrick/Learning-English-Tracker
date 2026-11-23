import { useOutletContext } from 'react-router'

import type { ProtectedRouteContext } from './ProtectedRoute'
import './session-status.css'

export default function SessionStatus() {
  const { user, signOutStatus, signOut } = useOutletContext<ProtectedRouteContext>()
  const isSigningOut = signOutStatus === 'pending'

  return (
    <div className="session-status" role="region" aria-label="Phiên đăng nhập" data-auth-status="authenticated">
      <p>Đã đăng nhập: <strong>{user.email}</strong></p>
      <button type="button" onClick={signOut} disabled={isSigningOut}>
        {isSigningOut ? 'Đang đăng xuất…' : 'Đăng xuất'}
      </button>
      {signOutStatus === 'failed' && (
        <p className="session-status__error" role="alert">
          Chưa xác nhận được đăng xuất. Vui lòng kiểm tra kết nối và thử lại.
        </p>
      )}
    </div>
  )
}
