import { useState, type FormEvent } from "react"
import { Link, useSearchParams } from "react-router"

import { Button } from "@/components/ui/button"
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { ApiError, api } from "@/lib/api"

export function ResetPassword() {
  const [params] = useSearchParams()
  const token = params.get("token") ?? ""
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(token ? null : "This reset link is not valid.")
  const [done, setDone] = useState(false)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    try {
      await api<void>("/v1/auth/reset", {
        method: "POST",
        body: JSON.stringify({ token, password }),
      })
      setDone(true)
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "This reset link is not valid.")
    }
  }

  return (
    <main className="mx-auto flex min-h-svh max-w-sm flex-col justify-center gap-12 px-6">
      <h1 className="text-[28px] leading-[1.14] tracking-[-0.022em]">Reset password</h1>
      {done ? (
        <p className="text-sm">
          Password saved.{" "}
          <Link to="/login" className="text-link underline-offset-4 hover:underline">
            Sign in
          </Link>
        </p>
      ) : (
        <form onSubmit={(event) => void onSubmit(event)}>
          <FieldGroup>
            <Field data-invalid={error ? true : undefined}>
              <FieldLabel htmlFor="password">New password</FieldLabel>
              <Input
                id="password"
                type="password"
                autoComplete="new-password"
                required
                minLength={8}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
              {error ? <FieldError>{error}</FieldError> : null}
            </Field>
            <Button type="submit" disabled={!token}>
              Save password
            </Button>
          </FieldGroup>
        </form>
      )}
    </main>
  )
}
