import { apiClient } from '../../shared/api/client.ts'
import { ApiError } from '../../shared/api/errors.ts'
import type { LoginInput, LoginResponse, RegisterInput, RegisterResponse } from './types.ts'

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function isRegisterResponse(value: unknown): value is RegisterResponse {
  if (!isRecord(value) || value.success !== true || typeof value.message !== 'string'
    || !isRecord(value.data)) return false

  const data = value.data
  return typeof data.id === 'string' && data.id.length > 0
    && typeof data.email === 'string' && data.email.length > 0
    && typeof data.first_name === 'string' && typeof data.last_name === 'string'
}

export async function registerAccount(
  input: RegisterInput,
  { signal }: { signal?: AbortSignal } = {},
): Promise<RegisterResponse> {
  // Tạo DTO mới để không gửi thêm field từ form; tuyệt đối không trim mật khẩu.
  const body: RegisterInput = {
    email: input.email.trim().toLowerCase(),
    password: input.password,
    password_confirm: input.password_confirm,
  }
  const response = await apiClient.request<unknown>('auth/register/', {
    method: 'POST',
    body,
    signal,
    // Request công khai: không truyền Bearer, không tạo hoặc lưu phiên sau đăng ký.
  })

  // JSON hợp lệ chưa chứng minh đúng contract; không báo tạo tài khoản thành công từ body lạ.
  if (!isRegisterResponse(response)) {
    throw new ApiError({ kind: 'invalid-response', code: 'invalid_register_response' })
  }

  return response
}

function isLoginResponse(value: unknown): value is LoginResponse {
  if (!isRecord(value) || typeof value.access !== 'string' || !value.access.trim()
    || typeof value.refresh !== 'string' || !value.refresh.trim() || !isRecord(value.user)) {
    return false
  }

  const user = value.user
  return typeof user.id === 'string' && user.id.trim().length > 0
    && typeof user.email === 'string' && user.email.trim().length > 0
    && typeof user.first_name === 'string' && typeof user.last_name === 'string'
    && typeof user.is_email_verified === 'boolean'
}

export async function loginAccount(
  input: LoginInput,
  { signal }: { signal?: AbortSignal } = {},
): Promise<LoginResponse> {
  // Giữ đúng hai field; Remember me chưa có contract. Không trim mật khẩu đăng nhập.
  const body: LoginInput = {
    email: input.email.trim().toLowerCase(),
    password: input.password,
  }
  const response = await apiClient.request<unknown>('auth/login/', {
    method: 'POST',
    body,
    signal,
  })

  if (!isLoginResponse(response)) {
    throw new ApiError({ kind: 'invalid-response', code: 'invalid_login_response' })
  }

  // Chỉ trả contract đã kiểm tra; không lưu token, gọi me/refresh hoặc tự chuyển trang.
  return response
}
