import { Eye } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router'

import illustration from '../../assets/auth/register-illustration.webp'
import graduationCap from '../../assets/auth/register-cap.png'
import emailIcon from '../../assets/auth/register-email.png'
import lockIcon from '../../assets/auth/register-lock.png'
import eyeOffIcon from '../../assets/auth/register-eye-off.png'
import FormField from '../../shared/ui/FormField'
import PasswordField from '../../shared/ui/PasswordField'
import { isAbortError } from '../../shared/api/errors'
import { registerAccount } from './api'
import { hasRegistrationErrors, mapRegistrationError, validateRegistration } from './registration'
import type { RegisterField, RegisterInput, RegistrationErrors } from './types'
import './auth.css'

const fieldOrder: readonly RegisterField[] = ['email', 'password', 'password_confirm']
const blankInput: RegisterInput = { email: '', password: '', password_confirm: '' }
const emptyErrors = (): RegistrationErrors => ({ fields: {}, form: [], requestId: null })

export default function RegisterPage() {
  const [input, setInput] = useState<RegisterInput>(blankInput)
  const [errors, setErrors] = useState<RegistrationErrors>(emptyErrors)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const emailRef = useRef<HTMLInputElement>(null)
  const passwordRef = useRef<HTMLInputElement>(null)
  const confirmationRef = useRef<HTMLInputElement>(null)
  const summaryRef = useRef<HTMLDivElement>(null)
  const focusTarget = useRef<RegisterField | 'summary' | null>(null)
  const pendingRequest = useRef<AbortController | null>(null)
  const navigate = useNavigate()

  useEffect(() => () => {
    // Rời trang: hủy request và bỏ response đến muộn, không cập nhật form đã unmount.
    pendingRequest.current?.abort()
    pendingRequest.current = null
  }, [])

  useEffect(() => {
    // Focus sau khi lỗi đã render; gõ sửa lỗi không tự nhảy sang field khác.
    const target = focusTarget.current
    focusTarget.current = null
    if (target === 'email') emailRef.current?.focus()
    else if (target === 'password') passwordRef.current?.focus()
    else if (target === 'password_confirm') confirmationRef.current?.focus()
    else if (target === 'summary') summaryRef.current?.focus()
  }, [errors])

  function showErrors(next: RegistrationErrors) {
    focusTarget.current = fieldOrder.find((field) => next.fields[field]?.length) ?? 'summary'
    setErrors(next)
  }

  function updateField(field: RegisterField, value: string) {
    // Chỉ chuẩn hóa email ở API boundary; không trim hoặc sửa nội dung password.
    setInput((previous) => ({ ...previous, [field]: value }))
    setErrors((previous) => ({
      // Password thay đổi làm kết quả so khớp cũ hết hiệu lực; kiểm tra lại ở lần submit sau.
      fields: { ...previous.fields, [field]: undefined, ...(field === 'password' ? { password_confirm: undefined } : {}) },
      form: [], requestId: null,
    }))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    // Ref khóa đồng bộ trước await, tránh hai request trong cùng nhịp click/Enter.
    if (pendingRequest.current) return
    const validation = validateRegistration(input)
    if (hasRegistrationErrors(validation)) {
      showErrors(validation)
      return
    }

    const controller = new AbortController()
    pendingRequest.current = controller
    setIsSubmitting(true)
    setErrors(emptyErrors())

    try {
      await registerAccount(input, { signal: controller.signal })
      if (controller.signal.aborted || pendingRequest.current !== controller) return

      // Register không cấp JWT. Chỉ mang cờ thông báo, không đưa password/email vào history.
      setInput(blankInput)
      navigate('/login', { replace: true, state: { registrationComplete: true } })
    } catch (error: unknown) {
      if (controller.signal.aborted || pendingRequest.current !== controller || isAbortError(error)) return
      showErrors(mapRegistrationError(error))
    } finally {
      if (pendingRequest.current === controller) {
        pendingRequest.current = null
        if (!controller.signal.aborted) setIsSubmitting(false)
      }
    }
  }

  const icon = (source: string, width: number, height: number) =>
    <img src={source} width={width} height={height} alt="" />
  const hasErrors = hasRegistrationErrors(errors)

  return (
    <section className="register-page" aria-labelledby="register-title">
      {/* Asset cắt pixel gốc theo lựa chọn người dùng; không dùng ảnh cả màn hình làm UI. */}
      <div className="register-page__visual" aria-hidden="true">
        <img src={illustration} width={755} height={1089} alt="" loading="lazy" decoding="async" />
      </div>
      <div className="register-page__panel">
        <div className="register-page__content">
          <header className="register-page__heading">
            <img src={graduationCap} width={136} height={111} alt="" />
            <h1 id="register-title">Register</h1>
          </header>

          <form className="register-form" noValidate aria-busy={isSubmitting} onSubmit={handleSubmit}>
            {hasErrors && (
              <div ref={summaryRef} className="auth-form-error" role="alert" tabIndex={-1}>
                {errors.form.length > 0
                  ? <ul>{errors.form.map((message, index) => <li key={index}>{message}</li>)}</ul>
                  : <p>Vui lòng kiểm tra các trường được đánh dấu bên dưới.</p>}
                {errors.requestId && <p className="auth-form-error__reference">Mã hỗ trợ: {errors.requestId}</p>}
              </div>
            )}

            <FormField
              ref={emailRef} id="register-email" name="email" label="Email" type="email"
              autoComplete="email" inputMode="email" autoCapitalize="none" spellCheck={false} maxLength={254} required
              value={input.email} errors={errors.fields.email} disabled={isSubmitting}
              leadingIcon={icon(emailIcon, 40, 39)}
              onChange={(event) => updateField('email', event.currentTarget.value)}
            />
            <PasswordField
              ref={passwordRef} id="register-password" name="password" label="Password"
              autoComplete="new-password" required value={input.password}
              errors={errors.fields.password} disabled={isSubmitting}
              leadingIcon={icon(lockIcon, 39, 40)} showIcon={icon(eyeOffIcon, 51, 51)}
              hideIcon={<Eye size={51} aria-hidden="true" />}
              onChange={(event) => updateField('password', event.currentTarget.value)}
            />
            <PasswordField
              ref={confirmationRef} id="register-password-confirm" name="password_confirm" label="Confirm password"
              autoComplete="new-password" required value={input.password_confirm}
              errors={errors.fields.password_confirm} disabled={isSubmitting}
              leadingIcon={icon(lockIcon, 39, 40)} showIcon={icon(eyeOffIcon, 51, 51)}
              hideIcon={<Eye size={51} aria-hidden="true" />}
              onChange={(event) => updateField('password_confirm', event.currentTarget.value)}
            />
            <button className="register-form__submit" type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Đang tạo tài khoản…' : 'Register'}
            </button>
          </form>
          {/* Live status ngoài aria-busy để công nghệ hỗ trợ không hoãn thông báo đang gửi. */}
          <span className="visually-hidden" role="status">
            {isSubmitting ? 'Đang gửi yêu cầu đăng ký.' : ''}
          </span>
          <p className="register-page__login">Already have an account? <Link to="/login">Login</Link></p>
        </div>
      </div>
    </section>
  )
}
