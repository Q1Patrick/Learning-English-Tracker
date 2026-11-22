import { isAbortError, isApiError } from '../../shared/api/errors.ts'
import type { SessionActionOptions, SignInOptions } from './AuthContext.ts'
import { createSession, deleteSession, fetchSession } from './session-api.ts'
import type { AuthState, LoginInput, SessionResponse } from './types.ts'

const checking: AuthState = Object.freeze({ status: 'checking', user: null, expiresAt: null })
const unavailable: AuthState = Object.freeze({ status: 'unavailable', user: null, expiresAt: null })
let snapshot: AuthState = checking
let csrfToken: string | null = null
let generation = 0
const listeners = new Set<() => void>()

interface SessionRead {
  generation: number
  controller: AbortController
  promise: Promise<void>
}

let activeRead: SessionRead | null = null
let mutationTail: Promise<void> = Promise.resolve()
let pendingMutations = 0
let recheckAfterMutation = false
let observers = 0
let channel: BroadcastChannel | null = null
let expiryTimer: ReturnType<typeof setTimeout> | null = null
let expiryHint: { expiresAt: number; deadline: number } | null = null
let checkedExpiry: number | null = null

function abortError(): DOMException {
  return new DOMException('Yêu cầu đã được hủy.', 'AbortError')
}

function stopExpiryTimer() {
  if (expiryTimer !== null) clearTimeout(expiryTimer)
  expiryTimer = null
}

function scheduleExpiry() {
  stopExpiryTimer()
  if (!observers || snapshot.status !== 'authenticated' || !expiryHint
    || checkedExpiry === expiryHint.expiresAt) return

  const hint = expiryHint
  // Dùng thời gian tương đối server cấp, không tin đồng hồ/exp do browser tự suy ra.
  const delay = Math.max(1000, hint.deadline - performance.now())
  expiryTimer = setTimeout(() => {
    expiryTimer = null
    if (snapshot.status !== 'authenticated' || expiryHint !== hint) return
    if (hint.deadline - performance.now() > 1000) {
      scheduleExpiry()
      return
    }
    // Một deadline chỉ tự kiểm tra một lần, tránh lặp GET nếu server còn xác nhận phiên.
    checkedExpiry = hint.expiresAt
    void requestSession({ replace: true })
  }, Math.min(delay, 2147483647))
}

function publish(next: AuthState) {
  snapshot = next
  scheduleExpiry()
  for (const listener of listeners) listener()
}

function applyResponse(response: SessionResponse, expectedGeneration: number): boolean {
  if (expectedGeneration !== generation) return false
  const data = response.data
  csrfToken = data.csrf_token
  if (data.authenticated && data.user !== null && data.expires_at !== null
    && data.expires_in !== null) {
    expiryHint = {
      expiresAt: data.expires_at,
      deadline: performance.now() + data.expires_in * 1000,
    }
    publish(Object.freeze({
      status: 'authenticated',
      user: Object.freeze({ ...data.user }),
      expiresAt: data.expires_at,
    }))
  } else {
    expiryHint = null
    checkedExpiry = null
    publish(Object.freeze({ status: 'anonymous', user: null, expiresAt: null }))
  }
  return true
}

function invalidateRead() {
  generation += 1
  activeRead?.controller.abort()
  activeRead = null
}

async function requestSession({ replace = false }: { replace?: boolean } = {}): Promise<void> {
  if (pendingMutations) {
    recheckAfterMutation = true
    return
  }
  if (replace) invalidateRead()
  if (activeRead?.generation === generation) return activeRead.promise

  const expectedGeneration = generation
  const controller = new AbortController()
  let operation: SessionRead
  const promise = fetchSession({ signal: controller.signal })
    .then((response) => {
      if (!controller.signal.aborted) applyResponse(response, expectedGeneration)
    })
    .catch((error: unknown) => {
      if (controller.signal.aborted || isAbortError(error) || expectedGeneration !== generation) return
      // Network/5xx/contract lỗi là chưa kiểm tra được phiên, không phải đã logout.
      csrfToken = null
      publish(unavailable)
    })
    .finally(() => {
      if (activeRead === operation) activeRead = null
    })
  operation = { generation: expectedGeneration, controller, promise }
  activeRead = operation
  return promise
}

function notifyOtherTabs() {
  try {
    // Cookie dùng chung theo origin; chỉ báo cần kiểm tra lại, không gửi user hoặc token.
    channel?.postMessage('session-changed')
  } catch {
    // Focus/visibility vẫn kiểm tra được phiên khi BroadcastChannel không khả dụng.
  }
}

function waitForCaller(operation: Promise<void>, signal?: AbortSignal): Promise<void> {
  if (!signal) return operation
  if (signal.aborted) return Promise.reject(abortError())
  return new Promise((resolve, reject) => {
    const onAbort = () => reject(abortError())
    signal.addEventListener('abort', onAbort, { once: true })
    operation.then(() => {
      signal.removeEventListener('abort', onAbort)
      if (signal.aborted) reject(abortError())
      else resolve()
    }, (error: unknown) => {
      signal.removeEventListener('abort', onAbort)
      reject(signal.aborted ? abortError() : error)
    })
  })
}

async function withMutationLock(run: () => Promise<void>): Promise<void> {
  const locks = typeof navigator === 'undefined' ? undefined : navigator.locks
  // Browser thiếu Web Locks vẫn serialize trong tab; focus/notification đối chiếu lại server.
  if (!locks) return run()
  let entered = false
  try {
    return await locks.request('learning-english-tracker-session-mutation', { mode: 'exclusive' }, () => {
      entered = true
      return run()
    })
  } catch (error: unknown) {
    if (entered) throw error // Không chạy lại mutation đã vào lock, kể cả khi POST thất bại.
    return run()
  }
}

function mutateSession(
  mutate: (token: string) => Promise<SessionResponse>,
  signal?: AbortSignal,
): Promise<void> {
  if (signal?.aborted) return Promise.reject(abortError())
  invalidateRead()
  const expectedGeneration = generation
  pendingMutations += 1
  csrfToken = null
  publish(checking)

  const operation = mutationTail.then(() => withMutationLock(async () => {
    let before: SessionResponse | null = null
    let postStarted = false
    try {
      if (signal?.aborted || expectedGeneration !== generation) throw abortError()
      // Lấy CSRF hiện tại sau mutation trước; tab khác có thể vừa login/rotate cookie.
      before = await fetchSession()
      if (signal?.aborted || expectedGeneration !== generation) throw abortError()
      csrfToken = before.data.csrf_token
      postStarted = true

      // Không abort POST theo vòng đời trang: server có thể đã commit và trả Set-Cookie.
      // Giữ request đến khi kết thúc để Login cũ không chạy sau Logout mới trong cùng tab.
      const response = await mutate(csrfToken)
      notifyOtherTabs()
      if (signal?.aborted || expectedGeneration !== generation) {
        recheckAfterMutation = true
        throw abortError()
      }
      applyResponse(response, expectedGeneration)
    } catch (error: unknown) {
      if (expectedGeneration === generation) {
        if (before && (!postStarted || (isApiError(error) && error.kind === 'http'
          && error.status !== null && error.status >= 400 && error.status < 500))) {
          // HTTP từ chối không phải logout thành công; giữ kết quả server vừa xác nhận.
          applyResponse(before, expectedGeneration)
        } else if (!isAbortError(error)) {
          csrfToken = null
          publish(unavailable)
        }
      }
      if (postStarted) {
        // Timeout/abort có kết quả server chưa rõ: GET đối chiếu, tuyệt đối không lặp POST.
        recheckAfterMutation = true
        if (!isApiError(error) || error.kind !== 'http') notifyOtherTabs()
      }
      if (isAbortError(error) && before === null) recheckAfterMutation = true
      throw error
    } finally {
      pendingMutations -= 1
      if (!pendingMutations && recheckAfterMutation) {
        recheckAfterMutation = false
        await requestSession()
      }
    }
  }))
  // Queue không bị kẹt sau lỗi; caller vẫn nhận lỗi gốc đã được API client làm sạch.
  mutationTail = operation.catch(() => undefined)
  return waitForCaller(operation, signal)
}

export function getAuthSnapshot(): AuthState {
  return snapshot
}

export function subscribeSession(listener: () => void): () => void {
  listeners.add(listener)
  return () => { listeners.delete(listener) }
}

export async function retrySession(): Promise<void> {
  publish(checking)
  await requestSession({ replace: true })
}

export function signInSession(input: LoginInput, options: SignInOptions = {}): Promise<void> {
  const submitted = { email: input.email, password: input.password }
  return mutateSession((token) => createSession(submitted, {
    csrfToken: token,
    rememberMe: options.rememberMe ?? false,
  }), options.signal)
}

export function signOutSession(options: SessionActionOptions = {}): Promise<void> {
  return mutateSession((token) => deleteSession(token), options.signal)
}

export function observeSession(): () => void {
  observers += 1
  if (observers > 1) return stopObserving

  const onFocus = () => {
    if (document.visibilityState === 'visible') void requestSession({ replace: true })
  }
  const onMessage = (event: MessageEvent<unknown>) => {
    if (event.data !== 'session-changed') return
    publish(checking)
    void requestSession({ replace: true })
  }
  window.addEventListener('focus', onFocus)
  document.addEventListener('visibilitychange', onFocus)
  try {
    if (typeof BroadcastChannel === 'function') {
      channel = new BroadcastChannel('learning-english-tracker-session')
      channel.addEventListener('message', onMessage)
    }
  } catch {
    channel = null
  }
  scheduleExpiry()
  if (!activeRead && !pendingMutations) void requestSession()

  detachObservation = () => {
    window.removeEventListener('focus', onFocus)
    document.removeEventListener('visibilitychange', onFocus)
    channel?.removeEventListener('message', onMessage)
    channel?.close()
    channel = null
    stopExpiryTimer()
  }
  return stopObserving
}

let detachObservation: (() => void) | null = null

function stopObserving() {
  observers -= 1
  if (observers) return
  detachObservation?.()
  detachObservation = null
  // StrictMode remount trong cùng lượt sẽ dùng lại GET đang chạy, không tạo bootstrap kép.
  queueMicrotask(() => {
    if (!observers) {
      activeRead?.controller.abort()
      activeRead = null
    }
  })
}
