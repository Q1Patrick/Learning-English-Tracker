// Kiểm tra API thật: chạy Django + Vite trước. Không tạo user, token hoặc dữ liệu học tập.
// Node hiện tại chạy được TypeScript trực tiếp; không cần thêm test framework.
import assert from 'node:assert/strict'
import { mkdir, writeFile } from 'node:fs/promises'

import { createApiClient } from '../src/shared/api/client.ts'
import { ApiError } from '../src/shared/api/errors.ts'

const baseUrl = process.env.API_VERIFY_BASE_URL || 'http://127.0.0.1:5173/api/v1/'
const report = {
  task: 'FE-03.2',
  timestamp: new Date().toISOString(),
  method: 'Real HTTP requests through Vite to the existing Django endpoints; no mocks/accounts/tokens',
  checks: [],
  notRun: ['Valid Bearer/login/refresh success (FE-03.4+)', 'Real HTTP 204/205', 'Non-JSON or malformed JSON success'],
}

async function check(name, action) {
  try {
    const evidence = await action()
    report.checks.push({ name, status: 'PASS', ...evidence })
    console.log(`PASS ${name}`)
  } catch (error) {
    report.checks.push({ name, status: 'FAIL' })
    // Chỉ in tên case; không dump request, credentials hoặc toàn bộ response lỗi.
    console.error(`FAIL ${name}`)
    throw error
  }
}

async function expectHttpError(api, endpoint, status, code, requiredFields = []) {
  try {
    await api.request(endpoint, requiredFields.length ? { method: 'POST', body: {} } : {})
    assert.fail('Expected an HTTP error')
  } catch (error) {
    assert.ok(error instanceof ApiError)
    assert.equal(error.kind, 'http')
    assert.equal(error.status, status)
    if (code) assert.equal(error.code, code)
    assert.match(error.requestId ?? '', /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
    for (const field of requiredFields) {
      assert.ok(Array.isArray(error.details?.[field]), `Missing validation messages: ${field}`)
    }
    return { httpStatus: error.status, code: error.code, requestId: error.requestId }
  }
}

try {
  const address = new URL(baseUrl)
  assert.ok(!address.username && !address.password && !address.search && !address.hash)
  report.apiOrigin = address.origin
  report.apiPath = address.pathname
  const api = createApiClient({ baseUrl })

  await check('Django health JSON is returned without unwrapping', async () => {
    const health = await api.request('health/')
    assert.equal(health.success, true)
    assert.equal(health.status, 'healthy')
    assert.equal(typeof health.message, 'string')
    assert.equal(health.data, undefined)
    return { httpStatus: 200, healthy: true }
  })

  await check('Query parameters reach the real health endpoint', async () => {
    const health = await api.request('health/?fe032=1')
    assert.equal(health.status, 'healthy')
    return { httpStatus: 200 }
  })

  await check('Anonymous current user is HTTP 401', () =>
    expectHttpError(api, 'auth/me/', 401, 'not_authenticated'))
  await check('Empty register preserves field validation errors', () =>
    expectHttpError(api, 'auth/register/', 400, 'validation_error', ['email', 'password', 'password_confirm']))
  await check('Empty login preserves field validation errors', () =>
    expectHttpError(api, 'auth/login/', 400, 'validation_error', ['email', 'password']))
  await check('Empty refresh preserves field validation errors', () =>
    expectHttpError(api, 'auth/token/refresh/', 400, 'validation_error', ['refresh']))
  await check('Submitted input cannot overwrite the server error code', async () => {
    // Thiếu email nên không chạm database; đây là input lỗi, không phải credential thật.
    await assert.rejects(api.request('auth/register/', {
      method: 'POST', body: { password: 'validation_error', password_confirm: '' },
    }), error => error instanceof ApiError && error.status === 400 && error.code === 'validation_error')
    return { httpStatus: 400, code: 'validation_error' }
  })
  await check('Django HTML 404 remains a safe HTTP error', async () => {
    const result = await expectHttpError(api, 'fe032-not-found/', 404)
    return result
  })

  await check('Unsupported response format remains HTTP 406', () =>
    expectHttpError(api, 'health/?format=api', 406, 'not_acceptable'))

  await check('Abort stays cancellation instead of a network error', async () => {
    const controller = new AbortController()
    controller.abort()
    await assert.rejects(api.request('health/', { signal: controller.signal }), error => error?.name === 'AbortError')
    return { errorName: 'AbortError' }
  })

  await check('Endpoint cannot escape the configured API root', async () => {
    const paths = ['https://example.com/', '//example.com/', '../health/', '%2e%2e/health/', 'auth\\me/', 'health/#fragment']
    for (const endpoint of paths) {
      await assert.rejects(async () => api.request(endpoint), error =>
        error instanceof ApiError && error.kind === 'configuration')
    }
    return { rejectedPaths: paths.length }
  })

  await check('Invalid base configuration cannot change the target origin', async () => {
    const bases = ['', 'api/v1/', '//example.com/api/', 'ftp://example.com/api/',
      'http://example.com/api/?q=1', 'http://example.com/api/#x', 'http://[invalid',
      'https://example.com//other.example/api/']
    for (const baseUrl of bases) {
      assert.throws(() => createApiClient({ baseUrl }), error =>
        error instanceof ApiError && error.kind === 'configuration')
    }
    return { rejectedConfigurations: bases.length }
  })

  report.status = 'PASS'
} catch (error) {
  report.status = 'FAIL'
  report.failureType = error?.name ?? 'Error'
  if (error instanceof ApiError) {
    report.failureKind = error.kind
    report.httpStatus = error.status
  }
  process.exitCode = 1
  console.error('API check failed. Verify Django/Vite addresses and inspect the named failing case.')
} finally {
  if (process.argv.includes('--save')) {
    const directory = new URL('../../docs/qa/fe-03.2/', import.meta.url)
    await mkdir(directory, { recursive: true })
    await writeFile(new URL('http-results.json', directory), `${JSON.stringify(report, null, 2)}\n`, 'utf8')
  }
  console.log(`${report.status}: ${report.checks.filter(check => check.status === 'PASS').length}/${report.checks.length} API checks passed`)
}
