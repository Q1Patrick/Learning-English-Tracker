import { useEffect, useMemo, useSyncExternalStore } from 'react'
import type { ReactNode } from 'react'
import { AuthContext } from './AuthContext.ts'
import {
  getAuthSnapshot,
  observeSession,
  retrySession,
  signInSession,
  signOutSession,
  subscribeSession,
} from './session.ts'

export default function AuthProvider({ children }: { children: ReactNode }) {
  const state = useSyncExternalStore(subscribeSession, getAuthSnapshot, getAuthSnapshot)
  useEffect(observeSession, [])
  const value = useMemo(() => ({
    ...state,
    retrySession,
    signIn: signInSession,
    signOut: signOutSession,
  }), [state])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
