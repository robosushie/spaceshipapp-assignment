import { useState, type FormEvent } from "react"
import { Link, Navigate } from "react-router"

import { LoginStory } from "@/components/LoginStory"
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
    <main className="grid min-h-svh md:grid-cols-2">
      <div className="order-2 md:order-1">
        <LoginStory />
      </div>
      <div className="order-1 flex flex-col justify-center px-6 py-12 md:order-2 md:px-10">
        <div className="mx-auto flex w-full max-w-sm flex-col gap-12">
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
              <Button variant="link" asChild>
                <Link to={email ? `/forgot-password?email=${encodeURIComponent(email)}` : "/forgot-password"}>
                  Forgot password
                </Link>
              </Button>
            </FieldGroup>
          </form>
        </div>
      </div>
    </main>
  )
}
