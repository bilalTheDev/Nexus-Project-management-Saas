import { createContext, useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '@/lib/api'
import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from '@/features/auth/auth-storage'

export const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [bootstrapping, setBootstrapping] = useState(true)

  const applySession = useCallback((payload) => {
    if (payload?.access) setAccessToken(payload.access)
    if (payload?.user) setUser(payload.user)
    return payload
  }, [])

  const clearSession = useCallback(() => {
    clearAccessToken()
    setUser(null)
  }, [])

  const refreshSession = useCallback(async () => {
    const { data } = await api.post('/auth/token/refresh/')
    setAccessToken(data.access)
    const me = await api.get('/users/me/')
    setUser(me.data)
    return me.data
  }, [])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        if (getAccessToken()) {
          const me = await api.get('/users/me/')
          if (!cancelled) setUser(me.data)
        } else {
          await refreshSession()
        }
      } catch {
        if (!cancelled) clearSession()
      } finally {
        if (!cancelled) setBootstrapping(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [clearSession, refreshSession])

  const login = useCallback(
    async ({ email, password }) => {
      const { data } = await api.post('/auth/token/', { email, password })
      return applySession(data)
    },
    [applySession],
  )

  const register = useCallback(
    async (payload) => {
      const { data } = await api.post('/auth/register/', payload)
      return applySession(data)
    },
    [applySession],
  )

  const logout = useCallback(async () => {
    try {
      await api.post('/auth/logout/')
    } catch {
      /* ignore */
    }
    clearSession()
  }, [clearSession])

  const value = useMemo(
    () => ({
      user,
      bootstrapping,
      isAuthenticated: Boolean(user),
      login,
      register,
      logout,
      refreshSession,
    }),
    [user, bootstrapping, login, register, logout, refreshSession],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
