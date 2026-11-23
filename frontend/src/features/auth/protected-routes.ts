import { matchPath, type To } from 'react-router'

export const protectedPaths = {
  dashboard: '/dashboard',
  vocabulary: '/vocabulary',
  studySessions: '/study-sessions',
  goals: '/goals',
  profile: '/profile',
} as const

export function getLoginDestination(state: unknown): To {
  if (typeof state !== 'object' || state === null || !('returnTo' in state)) {
    return protectedPaths.dashboard
  }

  // Xác thực history state trước khi dùng: pathname phải thuộc các route đã khai báo.
  const target = state.returnTo
  if (typeof target !== 'object' || target === null
    || !('pathname' in target) || !('search' in target) || !('hash' in target)) {
    return protectedPaths.dashboard
  }

  const { pathname, search, hash } = target
  if (typeof pathname !== 'string' || !Object.values(protectedPaths).some((path) => matchPath(path, pathname))
    || typeof search !== 'string' || (search !== '' && (!search.startsWith('?') || search.includes('#')))
    || typeof hash !== 'string' || (hash !== '' && !hash.startsWith('#'))) {
    return protectedPaths.dashboard
  }

  return { pathname, search, hash }
}
