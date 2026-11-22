// Register A chỉ gửi ba field; hồ sơ được hoàn thiện ở bước riêng sau đăng nhập.
export interface RegisterInput {
  email: string
  password: string
  password_confirm: string
}

export interface RegisterResponse {
  success: true
  message: string
  data: {
    id: string
    email: string
    first_name: string
    last_name: string
  }
}

export type RegisterField = keyof RegisterInput

export interface RegistrationErrors {
  fields: Partial<Record<RegisterField, string[]>>
  form: string[]
  requestId: string | null
}

// Login trả token và user trực tiếp; không có success/data hoặc profile ở endpoint này.
export interface LoginInput {
  email: string
  password: string
}

export interface LoginResponse {
  access: string
  refresh: string
  user: {
    id: string
    email: string
    first_name: string
    last_name: string
    is_email_verified: boolean
  }
}

export type LoginField = keyof LoginInput

export interface LoginErrors {
  fields: Partial<Record<LoginField, string[]>>
  form: string[]
  requestId: string | null
}

// Web session dùng cookie HttpOnly; giữ DTO JWT cũ cho client chưa chuyển đổi.
export interface SessionUser {
  readonly id: string
  readonly email: string
  readonly first_name: string
  readonly last_name: string
  readonly is_email_verified: boolean
}

export interface SessionResponse {
  success: true
  data: {
    authenticated: boolean
    user: SessionUser | null
    csrf_token: string
    expires_at: number | null
    expires_in: number | null
  }
}

// Lỗi kiểm tra phiên không có nghĩa server đã đăng xuất người dùng.
export type AuthState =
  | { readonly status: 'checking' | 'anonymous' | 'unavailable'; readonly user: null; readonly expiresAt: null }
  | { readonly status: 'authenticated'; readonly user: SessionUser; readonly expiresAt: number }
