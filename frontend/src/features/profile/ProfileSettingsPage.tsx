import { useEffect, useRef, useState } from 'react'

import { isApiError } from '../../shared/api/errors'
import { useAuth } from '../auth/useAuth'
import { fetchCurrentUser } from './api'
import type { CurrentUserProfile } from './types'
import './profile.css'

type ProfileState =
  | { status: 'loading' }
  | { status: 'ready'; data: CurrentUserProfile }
  | { status: 'error'; message: string; requestId: string | null; checkSession: boolean }

function describeLoadError(error: unknown): Extract<ProfileState, { status: 'error' }> {
  const failure = isApiError(error) ? error : null
  const checkSession = failure?.status === 401 || failure?.code === 'profile_account_mismatch'
  let message = 'Không thể tải hồ sơ. Vui lòng thử lại.'
  if (checkSession) message = 'Chưa thể xác nhận phiên để tải hồ sơ.'
  else if (failure?.code === 'profile_load_timeout') message = 'Tải hồ sơ quá thời gian chờ. Vui lòng thử lại.'
  else if (failure?.kind === 'network') message = 'Không thể kết nối để tải hồ sơ. Vui lòng kiểm tra kết nối.'
  else if (failure?.kind === 'invalid-response') message = 'Dữ liệu hồ sơ từ máy chủ không đúng định dạng.'

  return { status: 'error', message, requestId: failure?.requestId ?? null, checkSession }
}

function ProfileDetails({ data }: { data: CurrentUserProfile }) {
  const { email, profile } = data
  const fields = [
    { label: 'Email', value: email },
    { label: 'Tên hiển thị', value: profile?.displayName },
    { label: 'Trình độ tiếng Anh', value: profile?.englishLevel },
    { label: 'Mục tiêu mỗi ngày', value: profile ? `${profile.dailyTargetMinutes} phút` : undefined },
    { label: 'Múi giờ', value: profile?.timezone },
    { label: 'Mục tiêu học tập', value: profile?.learningGoal, wide: true },
  ]

  return (
    <>
      {profile === null && <p className="profile-settings__notice">Chưa có hồ sơ học tập.</p>}
      <dl className="profile-settings__details">
        {fields.map(({ label, value, wide }) => (
          <div key={label} className={wide ? 'profile-settings__goal' : undefined}>
            <dt>{label}</dt>
            <dd>{value?.trim() ? value : <span className="profile-settings__unset">Chưa thiết lập</span>}</dd>
          </div>
        ))}
      </dl>
    </>
  )
}

function ProfileContent({ userId, retrySession }: { userId: string; retrySession: () => Promise<void> }) {
  const [state, setState] = useState<ProfileState>({ status: 'loading' })
  const [attempt, setAttempt] = useState(0)
  const panelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const controller = new AbortController()
    void fetchCurrentUser(userId, controller.signal).then((data) => {
      if (!controller.signal.aborted) setState({ status: 'ready', data })
    }).catch((error: unknown) => {
      if (!controller.signal.aborted) setState(describeLoadError(error))
    })
    // Bỏ kết quả của lần tải đã rời trang, đổi tài khoản hoặc bị React StrictMode dọn dẹp.
    return () => controller.abort()
  }, [userId, attempt])

  function handleRetry() {
    if (state.status !== 'error') return
    if (state.checkSession) {
      // ProtectedRoute quyết định điều hướng theo Django. Chỉ kiểm tra lại khi người dùng yêu cầu.
      void retrySession()
      return
    }
    panelRef.current?.focus()
    setState({ status: 'loading' })
    setAttempt((previous) => previous + 1)
  }

  return (
    <div className="profile-settings__panel" ref={panelRef} tabIndex={-1}>
      {state.status === 'loading' && <p role="status">Đang tải hồ sơ…</p>}
      {state.status === 'error' && (
        <>
          <p role="alert">{state.message}</p>
          {state.requestId && <p className="profile-settings__notice">Mã hỗ trợ: {state.requestId}</p>}
          <button type="button" onClick={handleRetry}>{state.checkSession ? 'Kiểm tra phiên' : 'Thử lại'}</button>
        </>
      )}
      {state.status === 'ready' && <ProfileDetails data={state.data} />}
    </div>
  )
}

export default function ProfileSettingsPage() {
  const auth = useAuth()

  return (
    <section className="profile-settings" aria-labelledby="profile-settings-title">
      <h1 id="profile-settings-title">Hồ sơ và cài đặt</h1>
      {/* Key xóa state ngay khi ID đổi, trước khi effect mới bắt đầu tải hồ sơ. */}
      {auth.status === 'authenticated' && (
        <ProfileContent key={auth.user.id} userId={auth.user.id} retrySession={auth.retrySession} />
      )}
    </section>
  )
}
