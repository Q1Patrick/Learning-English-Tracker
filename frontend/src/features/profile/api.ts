import { apiClient } from '../../shared/api/client.ts'
import { ApiError } from '../../shared/api/errors.ts'
import type { CurrentUserProfile, LearningProfile } from './types.ts'

const profileTimeoutMs = 8_000

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function invalidProfileResponse() {
  return new ApiError({ kind: 'invalid-response', code: 'invalid_profile_response' })
}

function parseLearningProfile(value: unknown): LearningProfile | null {
  // Tài khoản cũ có thể chưa có bản ghi profile; null là kết quả hợp lệ từ Django.
  if (value === null) return null
  if (!isRecord(value) || typeof value.display_name !== 'string'
    || typeof value.english_level !== 'string' || typeof value.learning_goal !== 'string'
    || typeof value.timezone !== 'string' || typeof value.daily_target_minutes !== 'number'
    || !Number.isSafeInteger(value.daily_target_minutes) || value.daily_target_minutes < 0) {
    throw invalidProfileResponse()
  }

  return {
    displayName: value.display_name,
    englishLevel: value.english_level,
    dailyTargetMinutes: value.daily_target_minutes,
    learningGoal: value.learning_goal,
    timezone: value.timezone,
  }
}

export async function fetchCurrentUser(userId: string, signal: AbortSignal): Promise<CurrentUserProfile> {
  const timeout = AbortSignal.timeout(profileTimeoutMs)
  const requestSignal = AbortSignal.any([signal, timeout])
  let response: unknown
  try {
    // Session cookie do trình duyệt gửi cùng origin; GET không cần CSRF hoặc Bearer.
    response = await apiClient.request<unknown>('auth/me/', { session: true, signal: requestSignal })
  } catch (error: unknown) {
    if (timeout.aborted && requestSignal.reason === timeout.reason) {
      throw new ApiError({ kind: 'network', code: 'profile_load_timeout' })
    }
    throw error
  }

  if (!isRecord(response) || response.success !== true || !isRecord(response.data)) {
    throw invalidProfileResponse()
  }
  const { id, email, profile } = response.data
  if (typeof id !== 'number' || !Number.isSafeInteger(id) || id <= 0
    || typeof email !== 'string' || !email.trim()) {
    throw invalidProfileResponse()
  }

  // /me/ trả ID số, còn AuthProvider giữ ID chuỗi. So sánh trước khi chuyển dữ liệu sang UI.
  if (String(id) !== userId) {
    throw new ApiError({ kind: 'invalid-response', code: 'profile_account_mismatch' })
  }

  return { email, profile: parseLearningProfile(profile) }
}
