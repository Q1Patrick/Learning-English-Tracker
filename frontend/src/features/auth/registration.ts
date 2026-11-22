import { isAbortError, isApiError } from '../../shared/api/errors.ts'
import type { RegisterField, RegisterInput, RegistrationErrors } from './types.ts'

const registerFields: readonly RegisterField[] = ['email', 'password', 'password_confirm']

function emptyErrors(): RegistrationErrors {
  return { fields: {}, form: [], requestId: null }
}

export function validateRegistration(input: RegisterInput): RegistrationErrors {
  const errors = emptyErrors()
  const email = input.email.trim()

  if (!email) errors.fields.email = ['Vui lòng nhập email.']
  else if (!/^[^\s@]+@[^\s@]+$/.test(email)) {
    // Kiểm tra cơ bản; backend quyết định các quy tắc email còn lại.
    errors.fields.email = ['Vui lòng nhập email đúng định dạng.']
  }

  // Khoảng trắng vẫn thuộc mật khẩu: không trim và không tự thêm policy ngoài backend.
  if (!input.password) errors.fields.password = ['Vui lòng nhập mật khẩu.']
  if (!input.password_confirm) {
    errors.fields.password_confirm = ['Vui lòng xác nhận mật khẩu.']
  } else if (input.password !== input.password_confirm) {
    errors.fields.password_confirm = ['Mật khẩu xác nhận không khớp.']
  }

  return errors
}

export function hasRegistrationErrors(errors: RegistrationErrors): boolean {
  return errors.form.length > 0 || Object.values(errors.fields).some((messages) => Boolean(messages?.length))
}

function readMessages(value: unknown): string[] {
  if (typeof value === 'string') return value.trim() ? [value.trim()] : []
  if (!Array.isArray(value)) return []
  return value.flatMap((message: unknown) => typeof message === 'string' && message.trim()
    ? [message.trim()] : [])
}

export function mapRegistrationError(error: unknown): RegistrationErrors {
  const errors = emptyErrors()
  // Rời trang/hủy request không phải một lần đăng ký thất bại cần hiện thông báo.
  if (isAbortError(error)) return errors

  if (!isApiError(error)) {
    errors.form = ['Chưa thể xác nhận đăng ký. Vui lòng thử lại.']
    return errors
  }

  errors.requestId = error.requestId
  if (error.kind === 'http' && error.status === 400) {
    const details = typeof error.details === 'object' && error.details !== null
      && !Array.isArray(error.details) ? error.details as Record<string, unknown> : null

    if (details) {
      for (const field of registerFields) {
        const messages = readMessages(details[field])
        if (messages.length) errors.fields[field] = messages
      }
      // Password policy của Django có thể nằm ở non_field_errors, không phải password.
      errors.form = readMessages(details.non_field_errors)
    }

    if (error.code === 'duplicate_record' && !errors.fields.email?.length) {
      errors.fields.email = ['Email này đã được sử dụng. Hãy đăng nhập hoặc dùng email khác.']
    }

    if (!hasRegistrationErrors(errors)) {
      errors.form = ['Thông tin đăng ký chưa hợp lệ. Vui lòng kiểm tra lại.']
    }
    return errors
  }

  if (error.kind === 'network') {
    errors.form = ['Chưa xác nhận được đăng ký do lỗi kết nối. Vui lòng kiểm tra mạng và thử lại.']
  } else if (error.kind === 'http' && error.status !== null && error.status >= 500) {
    errors.form = ['Máy chủ chưa thể xác nhận đăng ký. Vui lòng thử lại sau.']
  } else if (error.kind === 'invalid-response') {
    errors.form = ['Chưa xác nhận được kết quả đăng ký. Hãy thử lại hoặc đăng nhập nếu tài khoản đã được tạo.']
  } else {
    errors.form = ['Không thể gửi yêu cầu đăng ký lúc này. Vui lòng thử lại sau.']
  }

  return errors
}
