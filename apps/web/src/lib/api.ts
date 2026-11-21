export class ApiError extends Error {
  status: number

  constructor(status: number, detail: string) {
    super(detail)
    this.status = status
  }
}

let accessToken: string | null = null

export function setAccessToken(token: string | null): void {
  accessToken = token
}

export function getAccessToken(): string | null {
  return accessToken
}

async function problemDetail(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string }
    return body.detail ?? "Request failed."
  } catch {
    return "Request failed."
  }
}

export async function api<T>(path: string, init?: RequestInit, retry = true): Promise<T> {
  const headers = new Headers(init?.headers)
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`)
  }
  if (init?.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json")
  }
  const response = await fetch(path, {
    ...init,
    headers,
    credentials: "include",
  })
  const isAuth = path.startsWith("/v1/auth/")
  if (response.status === 401 && retry && !isAuth) {
    const refreshed = await fetch("/v1/auth/refresh", {
      method: "POST",
      credentials: "include",
    })
    if (refreshed.ok) {
      const body = (await refreshed.json()) as { access_token: string }
      accessToken = body.access_token
      return api<T>(path, init, false)
    }
    accessToken = null
    throw new ApiError(401, "Authentication required.")
  }
  if (!response.ok) {
    throw new ApiError(response.status, await problemDetail(response))
  }
  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}
