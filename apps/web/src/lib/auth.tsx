import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react"

import { api, setAccessToken } from "@/lib/api"

type AuthValue = {
  ready: boolean
  signedIn: boolean
  signIn: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false)
  const [signedIn, setSignedIn] = useState(false)

  useEffect(() => {
    let cancelled = false
    api<{ access_token: string }>("/v1/auth/refresh", { method: "POST" }, false)
      .then((body) => {
        if (cancelled) {
          return
        }
        setAccessToken(body.access_token)
        setSignedIn(true)
      })
      .catch(() => {
        if (!cancelled) {
          setAccessToken(null)
          setSignedIn(false)
        }
      })
      .finally(() => {
        if (!cancelled) {
          setReady(true)
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

  const value = useMemo<AuthValue>(
    () => ({
      ready,
      signedIn,
      signIn: async (email, password) => {
        const body = await api<{ access_token: string }>(
          "/v1/auth/login",
          {
            method: "POST",
            body: JSON.stringify({ email, password }),
          },
          false,
        )
        setAccessToken(body.access_token)
        setSignedIn(true)
      },
      signOut: async () => {
        await api<void>("/v1/auth/logout", { method: "POST" }, false).catch(() => undefined)
        setAccessToken(null)
        setSignedIn(false)
      },
    }),
    [ready, signedIn],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthValue {
  const value = useContext(AuthContext)
  if (!value) {
    throw new Error("useAuth must be used inside AuthProvider")
  }
  return value
}
