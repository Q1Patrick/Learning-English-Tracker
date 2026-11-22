import { createContext } from 'react'
import type { AuthState, LoginInput } from './types.ts'

export interface SignInOptions {
  rememberMe?: boolean
  signal?: AbortSignal
}

export interface SessionActionOptions {
  signal?: AbortSignal
}

export type AuthContextValue = AuthState & {
  retrySession: () => Promise<void>
  signIn: (input: LoginInput, options?: SignInOptions) => Promise<void>
  signOut: (options?: SessionActionOptions) => Promise<void>
}

// Context chỉ giữ trạng thái/user/actions; CSRF ở coordinator, session ID do cookie HttpOnly quản lý.
export const AuthContext = createContext<AuthContextValue | null>(null)
