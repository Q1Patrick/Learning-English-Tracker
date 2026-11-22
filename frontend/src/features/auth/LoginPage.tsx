import { Eye } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router'

import illustration from '../../assets/auth/login-illustration.webp'
import emailIcon from '../../assets/auth/register-email.png'
import lockIcon from '../../assets/auth/register-lock.png'
import eyeOffIcon from '../../assets/auth/register-eye-off.png'
import logo from '../../assets/layout/logo.svg'
import { isAbortError } from '../../shared/api/errors'
import FormField from '../../shared/ui/FormField'
import PasswordField from '../../shared/ui/PasswordField'
import { hasLoginErrors, mapLoginError, validateLogin } from './login'
import { useAuth } from './useAuth'
import type { LoginErrors, LoginField, LoginInput } from './types'
import './auth.css'
import './login.css'

const fieldOrder: readonly LoginField[] = ['email', 'password']
const blankInput: LoginInput = { email: '', password: '' }
const emptyErrors = (): LoginErrors => ({ fields: {}, form: [], requestId: null })

export default function LoginPage() {
  const [input, setInput] = useState<LoginInput>(blankInput)
  const [errors, setErrors] = useState<LoginErrors>(emptyErrors)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)
  const auth = useAuth()
  const emailRef = useRef<HTMLInputElement>(null)
  const passwordRef = useRef<HTMLInputElement>(null)
  const summaryRef = useRef<HTMLDivElement>(null)
  const focusTarget = useRef<LoginField | 'summary' | null>(null)
  const pendingRequest = useRef<AbortController | null>(null)
  const navigate = useNavigate()

  // Giữ thông báo Register, chỉ đọc boolean; không nhận password/JWT qua router state.
  const navigationState: unknown = useLocation().state
  const registrationComplete = typeof navigationState === 'object' && navigationState !== null
    && 'registrationComplete' in navigationState && navigationState.registrationComplete === true

  useEffect(() => () => {
    pendingRequest.current?.abort()
    pendingRequest.current = null
  }, [])

  useEffect(() => {
    // Focus sau khi lỗi mount; sửa nội dung không làm focus nhảy khỏi field đang nhập.
    const target = focusTarget.current
    focusTarget.current = null
    if (target === 'email') emailRef.current?.focus()
    else if (target === 'password') passwordRef.current?.focus()
    else if (target === 'summary') summaryRef.current?.focus()
  }, [errors])

  function showErrors(next: LoginErrors) {
    focusTarget.current = fieldOrder.find((field) => next.fields[field]?.length) ?? 'summary'
    setErrors(next)
  }

  function updateField(field: LoginField, value: string) {
    setInput((previous) => ({ ...previous, [field]: value }))
    setErrors((previous) => ({ fields: { ...previous.fields, [field]: undefined }, form: [], requestId: null }))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    // Ref khóa ngay trước await: click/Enter liên tiếp vẫn chỉ tạo một request.
    if (pendingRequest.current) return
    const validation = validateLogin(input)
    if (hasLoginErrors(validation)) {
      showErrors(validation)
      return
    }

    const controller = new AbortController()
    pendingRequest.current = controller
    setIsSubmitting(true)
    setErrors(emptyErrors())
    try {
      await auth.signIn(input, { rememberMe, signal: controller.signal })
      if (controller.signal.aborted || pendingRequest.current !== controller) return

      // FE-03.5: Django giữ session server; Provider đã nhận user thật trước khi điều hướng.
      // Browser tự quản cookie HttpOnly, React không nhận hoặc lưu JWT/session ID.
      setInput(blankInput)
      navigate('/dashboard', { replace: true })
    } catch (error: unknown) {
      if (controller.signal.aborted || pendingRequest.current !== controller || isAbortError(error)) return
      showErrors(mapLoginError(error))
    } finally {
      if (pendingRequest.current === controller) {
        pendingRequest.current = null
        if (!controller.signal.aborted) setIsSubmitting(false)
      }
    }
  }

  const icon = (source: string, width: number, height: number) =>
    <img src={source} width={width} height={height} alt="" />

  return (
    <section className="login-page" aria-labelledby="login-title">
      <div className="login-page__art" aria-hidden="true">
        <img src={illustration} width={819} height={873} alt="" loading="lazy" decoding="async" />
      </div>
      <div className="login-page__card">
        <header className="login-page__heading">
          <img src={logo} width={48} height={48} alt="" />
          <h1 id="login-title">Learning English<br />Tracker</h1>
        </header>
        {registrationComplete && (
          <p className="auth-registration-notice" role="status">
            Tạo tài khoản thành công. Hãy đăng nhập để tiếp tục.
          </p>
        )}
        <h2 className="login-page__prompt" id="login-form-title">Login to your account</h2>
        <form className="login-form" aria-labelledby="login-form-title" noValidate aria-busy={isSubmitting} onSubmit={handleSubmit}>
          {hasLoginErrors(errors) && (
            <div ref={summaryRef} className="auth-form-error" role="alert" tabIndex={-1}>
              {errors.form.length
                ? <ul>{errors.form.map((message, index) => <li key={index}>{message}</li>)}</ul>
                : <p>Vui lòng kiểm tra các trường được đánh dấu bên dưới.</p>}
              {errors.requestId && <p className="auth-form-error__reference">Mã hỗ trợ: {errors.requestId}</p>}
            </div>
          )}
          <FormField
            ref={emailRef} id="login-email" name="email" label="Email" placeholder="Email" type="email"
            autoComplete="username" inputMode="email" autoCapitalize="none" spellCheck={false} maxLength={254} required
            value={input.email} errors={errors.fields.email} disabled={isSubmitting}
            leadingIcon={icon(emailIcon, 40, 39)}
            onChange={(event) => updateField('email', event.currentTarget.value)}
          />
          <PasswordField
            ref={passwordRef} id="login-password" name="password" label="Password" placeholder="Password"
            autoComplete="current-password" required value={input.password}
            errors={errors.fields.password} disabled={isSubmitting}
            leadingIcon={icon(lockIcon, 39, 40)} showIcon={icon(eyeOffIcon, 51, 51)}
            hideIcon={<Eye size={32} aria-hidden="true" />}
            onChange={(event) => updateField('password', event.currentTarget.value)}
          />
          {/* Remember me có contract session thật; reset password vẫn là feature riêng chưa triển khai. */}
          <div className="login-form__support">
            <div className="login-form__options">
              <label className="login-form__remember">
                <input
                  type="checkbox" checked={rememberMe} disabled={isSubmitting}
                  onChange={(event) => setRememberMe(event.currentTarget.checked)}
                  aria-describedby="login-support-note"
                />
                <span>Remember me</span>
              </label>
              <button className="login-form__forgot" type="button" disabled aria-describedby="login-support-note">Forgot password?</button>
            </div>
            <p id="login-support-note">Remember me giữ phiên lâu hơn trên thiết bị cá nhân. Đặt lại mật khẩu chưa khả dụng.</p>
          </div>
          <button className="login-form__submit" type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Đang đăng nhập…' : 'Login'}
          </button>
        </form>
        {/* Ngoài aria-busy để thông báo đang gửi được đọc ngay. */}
        <span className="visually-hidden" role="status">{isSubmitting ? 'Đang gửi yêu cầu đăng nhập.' : ''}</span>
        <p className="login-page__register">Chưa có tài khoản? <Link to="/register">Sign up</Link></p>
      </div>
    </section>
  )
}
