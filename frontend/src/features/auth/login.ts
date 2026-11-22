import { isAbortError, isApiError } from '../../shared/api/errors.ts'
import type { LoginErrors, LoginField, LoginInput } from './types.ts'

const loginFields: readonly LoginField[] = ['email', 'password']

function emptyErrors(): LoginErrors {
  return { fields: {}, form: [], requestId: null }
}

export function validateLogin(input: LoginInput): LoginErrors {
  const errors = emptyErrors()
  const email = input.email.trim()

  if (!email) errors.fields.email = ['Vui lòng nhập email.']
  else if (!/^[^\s@]+@[^\s@]+$/.test(email)) {
    errors.fields.email = ['Vui lòng nhập email đúng định dạng.']
  }

  // Login kiểm tra mật khẩu hiện có, không áp dụng lại policy tạo mật khẩu mới.
  if (!input.password) errors.fields.password = ['Vui lòng nhập mật khẩu.']
  return errors
}

export function hasLoginErrors(errors: LoginErrors): boolean {
  return errors.form.length > 0 || Object.values(errors.fields).some((messages) => Boolean(messages?.length))
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function readMessages(value: unknown): string[] {
  if (typeof value === 'string') return value.trim() ? [value.trim()] : []
  if (!Array.isArray(value)) return []
  return value.flatMap((message: unknown) => typeof message === 'string' && message.trim()
    ? [message.trim()] : [])
}

export function mapLoginError(error: unknown): LoginErrors {
  const errors = emptyErrors()
  if (isAbortError(error)) return errors

  if (!isApiError(error)) {
    errors.form = ['Chưa thể xác nhận đăng nhập. Vui lòng thử lại.']
    return errors
  }

  errors.requestId = error.requestId
  if (error.kind === 'http' && error.status === 401) {
    // Không hiển thị lý do tài khoản tồn tại/không hoạt động từ response credentials.
    errors.form = ['Email hoặc mật khẩu không đúng.']
    return errors
  }

  if (error.kind === 'http' && error.status === 400) {
    if (isRecord(error.details)) {
      for (const field of loginFields) {
        const messages = readMessages(error.details[field])
        if (messages.length) errors.fields[field] = messages
      }
      errors.form = readMessages(error.details.non_field_errors)
    }

    if (!hasLoginErrors(errors)) errors.form = ['Thông tin đăng nhập chưa hợp lệ. Vui lòng kiểm tra lại.']
    return errors
  }

  if (error.kind === 'network') {
    errors.form = ['Chưa xác nhận được đăng nhập do lỗi kết nối. Vui lòng kiểm tra mạng và thử lại.']
  } else if (error.kind === 'http' && error.status !== null && error.status >= 500) {
    errors.form = ['Máy chủ chưa thể xác nhận đăng nhập. Vui lòng thử lại sau.']
  } else if (error.kind === 'invalid-response') {
    errors.form = ['Chưa nhận được kết quả đăng nhập hợp lệ. Vui lòng thử lại sau.']
  } else {
    errors.form = ['Không thể gửi yêu cầu đăng nhập lúc này. Vui lòng thử lại sau.']
  }

  return errors
}
