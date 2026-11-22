import { ApiError, isAbortError, redactErrorDetails } from './errors.ts'

export type ApiMethod = 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE'

export interface ApiRequestOptions {
  method?: ApiMethod
  body?: unknown
  accessToken?: string
  signal?: AbortSignal
  // Chỉ bật cho luồng web cùng origin: browser quản lý cookie HttpOnly, JS không đọc session ID.
  session?: boolean
  csrfToken?: string
}

export interface ApiClientOptions {
  baseUrl?: string
}

export interface ApiClient {
  request<T = unknown>(endpoint: string, options?: ApiRequestOptions): Promise<T>
}

const parsingOrigin = 'https://api-client.invalid'
const methods: readonly string[] = ['GET', 'POST', 'PATCH', 'PUT', 'DELETE']
const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
const configuredBaseUrl: unknown = import.meta.env?.VITE_API_BASE_URL

function configurationError(code: string): ApiError {
  return new ApiError({ kind: 'configuration', code })
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function hasControlCharacters(value: string, includeSpace = false): boolean {
  for (let index = 0; index < value.length; index += 1) {
    const code = value.charCodeAt(index)
    if (code <= (includeSpace ? 32 : 31) || code === 127) return true
  }
  return false
}

function hasUnsafePath(path: string): boolean {
  // Không nhận slash/backslash/percent được mã hóa: tránh các lớp giải mã khác nhau ở proxy.
  if (hasControlCharacters(path, true) || path.includes('\\') || /%(?:2f|5c|25)/i.test(path)) return true

  try {
    const decoded = decodeURIComponent(path)
    return hasControlCharacters(decoded, true) || decoded.includes('\\')
      || decoded.split('/').some((segment) => segment === '.' || segment === '..')
  } catch {
    return true
  }
}

function parseBaseUrl(baseUrl: string) {
  if (typeof baseUrl !== 'string') throw configurationError('invalid_base_url')
  const value = baseUrl.trim()
  const absolute = /^https?:\/\//i.test(value)

  if (!value || /[?#]/.test(value) || hasUnsafePath(value)
    || (!absolute && (!value.startsWith('/') || value.startsWith('//')))) {
    throw configurationError('invalid_base_url')
  }

  let parsed: URL
  try {
    parsed = new URL(value, parsingOrigin)
  } catch {
    throw configurationError('invalid_base_url')
  }

  // Path bắt đầu // có thể bị hiểu là authority mới khi ghép URL.
  if (!['http:', 'https:'].includes(parsed.protocol) || parsed.username || parsed.password
    || parsed.pathname.startsWith('//')) {
    throw configurationError('invalid_base_url')
  }

  const pathname = `${parsed.pathname.replace(/\/+$/, '')}/`
  return { absolute, root: new URL(pathname, parsed.origin), pathname }
}

function resolveEndpoint(endpoint: string, base: ReturnType<typeof parseBaseUrl>): string {
  if (typeof endpoint !== 'string' || !endpoint || hasControlCharacters(endpoint) || endpoint.includes('#')
    || /^[a-z][a-z\d+.-]*:/i.test(endpoint) || endpoint.startsWith('//')) {
    throw configurationError('invalid_endpoint')
  }

  const queryIndex = endpoint.indexOf('?')
  const path = queryIndex < 0 ? endpoint : endpoint.slice(0, queryIndex)
  const query = queryIndex < 0 ? '' : endpoint.slice(queryIndex)

  if (hasUnsafePath(path)) throw configurationError('invalid_endpoint')

  const decodedPath = decodeURIComponent(path)
  if (/^[a-z][a-z\d+.-]*:/i.test(decodedPath) || decodedPath.startsWith('//')) {
    throw configurationError('invalid_endpoint')
  }

  const relativePath = path.replace(/^\//, '')
  if (!relativePath) throw configurationError('invalid_endpoint')

  // Một dấu / đầu vẫn là endpoint tương đối; dấu / cuối luôn đứng trước query.
  const target = new URL(`${relativePath.replace(/\/+$/, '')}/${query}`, base.root)
  if (target.origin !== base.root.origin || !target.pathname.startsWith(base.pathname)) {
    throw configurationError('invalid_endpoint')
  }

  return base.absolute ? target.href : `${target.pathname}${target.search}`
}

function getCredentials(body: unknown, accessToken: string | undefined): string[] {
  const values = accessToken ? [accessToken] : []
  if (!isRecord(body)) return values

  for (const [key, value] of Object.entries(body)) {
    if (/^(?:password|password_confirm|access|refresh|token|authorization|api_key|secret)$/i.test(key)
      && typeof value === 'string' && value) {
      values.push(value)
    }
  }

  return values
}

function readRequestId(header: string | null, body: unknown, credentials: readonly string[]): string | null {
  const candidates: unknown[] = [header, isRecord(body) ? body.request_id : null]
  return candidates.find((value): value is string =>
    typeof value === 'string' && uuidPattern.test(value) && !credentials.includes(value),
  ) ?? null
}

export function createApiClient({ baseUrl }: ApiClientOptions = {}): ApiClient {
  const defaultBaseUrl = typeof configuredBaseUrl === 'string' && configuredBaseUrl.trim()
    ? configuredBaseUrl : '/api/v1'
  const base = parseBaseUrl(baseUrl ?? defaultBaseUrl)

  return {
    async request<T = unknown>(endpoint: string, options: ApiRequestOptions = {}): Promise<T> {
      const target = resolveEndpoint(endpoint, base)
      const method = options.method ?? 'GET'
      const requestBody = options.body
      const accessToken = options.accessToken
      const signal = options.signal
      if (!methods.includes(method)) throw configurationError('invalid_method')
      if (method === 'GET' && requestBody !== undefined) throw configurationError('invalid_get_body')

      const session = options.session === true
      if (session && accessToken !== undefined) throw configurationError('mixed_authentication_modes')
      if (!session && options.csrfToken !== undefined) throw configurationError('csrf_without_session')
      // Cookie/CSRF không được gửi sang origin khác do cấu hình API base bị đổi.
      // Production dùng reverse proxy /api/ cùng origin như Vite trong development.
      if (session && base.absolute
        && (typeof globalThis.location === 'undefined' || new URL(target).origin !== globalThis.location.origin)) {
        throw configurationError('cross_origin_session_request')
      }

      const headers = new Headers({ Accept: 'application/json' })
      if (options.csrfToken !== undefined) {
        if (typeof options.csrfToken !== 'string'
          || !/^(?:[A-Za-z0-9]{32}|[A-Za-z0-9]{64})$/.test(options.csrfToken)) {
          throw configurationError('invalid_csrf_token')
        }
        if (method !== 'GET') headers.set('X-CSRFToken', options.csrfToken)
      }
      if (accessToken !== undefined) {
        if (typeof accessToken !== 'string' || !/^[A-Za-z0-9._~+/-]+=*$/.test(accessToken)) {
          throw configurationError('invalid_access_token')
        }
        headers.set('Authorization', `Bearer ${accessToken}`)
      }

      let body: string | undefined
      if (requestBody !== undefined) {
        try {
          body = JSON.stringify(requestBody)
        } catch {
          throw configurationError('invalid_json_body')
        }
        if (body === undefined) throw configurationError('invalid_json_body')
        headers.set('Content-Type', 'application/json')
      }
      const credentials = getCredentials(requestBody, accessToken)
      if (options.csrfToken) credentials.push(options.csrfToken)

      let response: Response
      let text: string
      try {
        response = await globalThis.fetch(target, {
          method,
          headers,
          body,
          signal,
          credentials: session ? 'same-origin' : 'omit',
          redirect: 'error',
        })
        // 204/205 không có payload: caller dùng request<void>, không gọi JSON.parse.
        if (response.status === 204 || response.status === 205) return undefined as T
        text = await response.text()
      } catch (error: unknown) {
        if (isAbortError(error) || signal?.aborted) throw error
        // Không giữ TypeError/cause vì trình duyệt có thể đưa URL hoặc credentials vào message.
        throw new ApiError({ kind: 'network', code: 'network_error' })
      }

      const contentType = response.headers.get('Content-Type')?.split(';')[0].trim().toLowerCase()
      const isJson = contentType === 'application/json'
        || Boolean(contentType?.startsWith('application/') && contentType.endsWith('+json'))
      let payload: unknown
      let parsed = false
      if (isJson && text.trim()) {
        try {
          payload = JSON.parse(text)
          parsed = true
        } catch {
          // HTTP failure vẫn giữ status; success bị lỗi JSON được phân loại riêng bên dưới.
        }
      }

      const requestId = readRequestId(response.headers.get('X-Request-ID'), payload, credentials)
      if (!response.ok) {
        const error = isRecord(payload) && payload.success === false && isRecord(payload.error)
          ? payload.error : null
        // Machine code do backend định nghĩa; không thay đổi vì trùng dữ liệu người dùng nhập.
        const errorCode = error?.code
        throw new ApiError({
          kind: 'http',
          status: response.status,
          code: typeof errorCode === 'string' && /^[a-z][a-z\d_]{0,79}$/i.test(errorCode)
            ? errorCode : 'http_error',
          details: error ? redactErrorDetails(error.details, credentials) : null,
          requestId,
        })
      }

      // Ngoài 204/205, success rỗng hoặc không phải JSON là contract lỗi, không giả thành công.
      if (!parsed) {
        throw new ApiError({ kind: 'invalid-response', status: response.status, code: 'invalid_response', requestId })
      }

      return payload as T
    },
  }
}

export const apiClient = createApiClient()
