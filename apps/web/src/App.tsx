import type { ReactNode } from "react"
import { Navigate, Route, Routes } from "react-router"

import { DeskFrame } from "@/components/DeskFrame"
import { Skeleton } from "@/components/ui/skeleton"
import { useAuth } from "@/lib/auth"
import { AcceptInvite } from "@/pages/AcceptInvite"
import { Dashboard } from "@/pages/Dashboard"
import { Details } from "@/pages/Details"
import { ForgotPassword } from "@/pages/ForgotPassword"
import { Login } from "@/pages/Login"
import { ResetPassword } from "@/pages/ResetPassword"
import { Settings } from "@/pages/Settings"

function Gate({ children }: { children: ReactNode }) {
  const { ready, signedIn } = useAuth()
  if (!ready) {
    return (
      <main className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-8">
        <Skeleton className="h-10 w-40" />
        <Skeleton className="h-64 w-full" />
      </main>
    )
  }
  if (!signedIn) {
    return <Navigate to="/login" replace />
  }
  return children
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/accept-invite" element={<AcceptInvite />} />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route
        element={
          <Gate>
            <DeskFrame />
          </Gate>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/details" element={<Details />} />
      </Route>
      <Route
        path="/settings"
        element={
          <Gate>
            <Settings />
          </Gate>
        }
      />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
