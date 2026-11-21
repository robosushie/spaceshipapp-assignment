import type { ReactNode } from "react"
import { Navigate, Route, Routes } from "react-router"

import { Skeleton } from "@/components/ui/skeleton"
import { useAuth } from "@/lib/auth"
import { Desk } from "@/pages/Desk"
import { Login } from "@/pages/Login"

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
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route
        path="/dashboard"
        element={
          <Gate>
            <Desk />
          </Gate>
        }
      />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
