import { useState, type FormEvent } from "react"
import { Link, useSearchParams } from "react-router"

import { Button } from "@/components/ui/button"
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { ApiError, api } from "@/lib/api"

const SENT = "If that email has an account, a reset link is on its way."

export function ForgotPassword() {
  const [params] = useSearchParams()
  const [email, setEmail] = useState(params.get("email") ?? "")
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setPending(true)
    setError(null)
    setNotice(null)
    try {
      await api<void>("/v1/auth/forgot", {
        method: "POST",
        body: JSON.stringify({ email }),
      })
      setNotice(SENT)
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "The reset email could not be sent.")
    } finally {
      setPending(false)
    }
  }

  return (
    <main className="mx-auto flex min-h-svh max-w-sm flex-col justify-center gap-12 px-6">
      <h1 className="text-[28px] leading-[1.14] tracking-[-0.022em]">Forgot password</h1>
      <form onSubmit={(event) => void onSubmit(event)}>
        <FieldGroup>
          <Field data-invalid={error ? true : undefined}>
            <FieldLabel htmlFor="email">Email</FieldLabel>
            <Input
              id="email"
              type="email"
              autoComplete="username"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
            {error ? <FieldError>{error}</FieldError> : null}
            {notice ? <p className="text-sm text-muted-foreground">{notice}</p> : null}
          </Field>
          <Button type="submit" disabled={pending}>
            Send reset link
          </Button>
          <Button variant="link" asChild>
            <Link to="/login">Back to sign in</Link>
          </Button>
        </FieldGroup>
      </form>
    </main>
  )
}
