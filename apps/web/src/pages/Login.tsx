import { useState, type FormEvent } from "react"
import { Navigate } from "react-router"

import { Button } from "@/components/ui/button"
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { ApiError } from "@/lib/api"
import { useAuth } from "@/lib/auth"

export function Login() {
  const { signedIn, signIn } = useAuth()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  if (signedIn) {
    return <Navigate to="/dashboard" replace />
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setPending(true)
    setError(null)
    try {
      await signIn(email, password)
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Sign in failed.")
    } finally {
      setPending(false)
    }
  }

  return (
    <main className="mx-auto flex min-h-svh max-w-sm flex-col justify-center gap-12 px-6">
      <h1 className="text-[49px] leading-[1.2] tracking-[-0.027em]">Spaceship</h1>
      <form onSubmit={onSubmit}>
        <FieldGroup>
          <Field data-invalid={error ? true : undefined}>
            <FieldLabel htmlFor="email">Email</FieldLabel>
            <Input
              id="email"
              type="email"
              autoComplete="username"
              required
              value={email}
              aria-invalid={error ? true : undefined}
              onChange={(event) => setEmail(event.target.value)}
            />
          </Field>
          <Field data-invalid={error ? true : undefined}>
            <FieldLabel htmlFor="password">Password</FieldLabel>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              aria-invalid={error ? true : undefined}
              onChange={(event) => setPassword(event.target.value)}
            />
            {error ? <FieldError>{error}</FieldError> : null}
          </Field>
          <Button type="submit" disabled={pending}>
            Sign in
          </Button>
        </FieldGroup>
      </form>
    </main>
  )
}
