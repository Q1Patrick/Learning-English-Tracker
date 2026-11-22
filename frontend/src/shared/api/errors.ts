export type ApiErrorKind = 'http' | 'network' | 'invalid-response' | 'configuration'

interface ApiErrorOptions {
  kind: ApiErrorKind
  status?: number | null
  code?: string | null
  details?: unknown
  requestId?: string | null
}

const messages: Record<ApiErrorKind, string> = {
  http: 'Yêu cầu API không thành công.',
  network: 'Không thể kết nối tới API. Hãy kiểm tra kết nối và thử lại.',
  'invalid-response': 'API trả về dữ liệu không đúng định dạng JSON mong đợi.',
  configuration: 'Cấu hình hoặc dữ liệu gửi API không hợp lệ.',
}

// Chỉ giữ thông tin cần xử lý lỗi; không giữ request, Response, URL hoặc exception gốc.
export class ApiError extends Error {
  readonly kind: ApiErrorKind
  readonly status: number | null
  readonly code: string | null
  readonly details: unknown
  readonly requestId: string | null

  constructor({ kind, status = null, code = null, details = null, requestId = null }: ApiErrorOptions) {
    super(messages[kind])
    this.name = 'ApiError'
    this.kind = kind
    this.status = status
    this.code = code
    this.details = details
    this.requestId = requestId
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError
}

export function isAbortError(error: unknown): boolean {
  return typeof error === 'object' && error !== null && 'name' in error && error.name === 'AbortError'
}

// Giữ tên field và câu validation, chỉ che giá trị credentials nếu server vô tình phản chiếu.
export function redactErrorDetails(value: unknown, credentials: readonly string[], depth = 0): unknown {
  if (depth > 8) return null

  if (typeof value === 'string') {
    let redacted = value
      .replace(/\bBearer\s+\S+/gi, 'Bearer [REDACTED]')
      .replace(/\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b/g, '[REDACTED]')

    for (const credential of credentials) {
      if (credential.length >= 8) redacted = redacted.replaceAll(credential, '[REDACTED]')
      else if (credential && redacted === credential) redacted = '[REDACTED]'
    }

    return redacted
  }

  if (Array.isArray(value)) {
    return value.map((item: unknown) => redactErrorDetails(item, credentials, depth + 1))
  }

  if (typeof value === 'object' && value !== null) {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]: [string, unknown]) => [
        key,
        redactErrorDetails(item, credentials, depth + 1),
      ]),
    )
  }

  return value
}
