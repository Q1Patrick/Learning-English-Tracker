import { apiClient } from '../../shared/api/client.ts'
import { ApiError } from '../../shared/api/errors.ts'
import type { LoginInput, SessionResponse, SessionUser } from './types.ts'

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function isSessionUser(value: unknown): value is SessionUser {
  if (!isRecord(value)) return false
  return typeof value.id === 'string' && /^[1-9][0-9]*$/.test(value.id)
    && typeof value.email === 'string' && value.email.length > 0 && value.email.length <= 254
    && value.email === value.email.trim()
    && typeof value.first_name === 'string' && typeof value.last_name === 'string'
    && typeof value.is_email_verified === 'boolean'
}

function parseSessionResponse(value: unknown): SessionResponse {
  if (!isRecord(value) || value.success !== true || !isRecord(value.data)) {
    throw new ApiError({ kind: 'invalid-response', code: 'invalid_session_response' })
  }
  const data = value.data
  const validCsrf = typeof data.csrf_token === 'string' && /^[A-Za-z0-9]{64}$/.test(data.csrf_token)
  const validExpiry = typeof data.expires_at === 'number' && Number.isSafeInteger(data.expires_at)
    && data.expires_at > 0 && typeof data.expires_in === 'number'
    && Number.isFinite(data.expires_in) && data.expires_in >= 0
  if (!validCsrf || typeof data.authenticated !== 'boolean'
    || (data.authenticated
      ? !isSessionUser(data.user) || !validExpiry
      : data.user !== null || data.expires_at !== null || data.expires_in !== null)) {
    throw new ApiError({ kind: 'invalid-response', code: 'invalid_session_response' })
  }

  // Chỉ giữ field thuộc contract; không đưa payload dư hoặc token vào UI state.
  const user = data.authenticated && isSessionUser(data.user) ? {
    id: data.user.id,
    email: data.user.email,
    first_name: data.user.first_name,
    last_name: data.user.last_name,
    is_email_verified: data.user.is_email_verified,
  } : null
  return {
    success: true,
    data: {
      authenticated: data.authenticated,
      user,
      csrf_token: data.csrf_token as string,
      expires_at: data.expires_at as number | null,
      expires_in: data.expires_in as number | null,
    },
  }
}

export async function fetchSession({ signal }: { signal?: AbortSignal } = {}): Promise<SessionResponse> {
  return parseSessionResponse(await apiClient.request<unknown>('auth/session/', {
    session: true,
    signal,
  }))
}

export async function createSession(
  input: LoginInput,
  { csrfToken, rememberMe = false }: { csrfToken: string; rememberMe?: boolean },
): Promise<SessionResponse> {
  const response = parseSessionResponse(await apiClient.request<unknown>('auth/session/login/', {
    method: 'POST',
    session: true,
    csrfToken,
    body: {
      email: input.email.trim().toLowerCase(),
      password: input.password,
      remember_me: rememberMe,
    },
  }))
  if (!response.data.authenticated) {
    throw new ApiError({ kind: 'invalid-response', code: 'invalid_session_login_response' })
  }
  return response
}

export async function deleteSession(csrfToken: string): Promise<SessionResponse> {
  const response = parseSessionResponse(await apiClient.request<unknown>('auth/session/logout/', {
    method: 'POST',
    session: true,
    csrfToken,
    body: {},
  }))
  if (response.data.authenticated) {
    throw new ApiError({ kind: 'invalid-response', code: 'invalid_session_logout_response' })
  }
  return response
}
