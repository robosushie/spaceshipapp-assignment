import type { ReactNode } from "react"
import { LayoutDashboardIcon, ListIcon, LogOutIcon, RocketIcon, SettingsIcon } from "lucide-react"
import { Link } from "react-router"

import { Button } from "@/components/ui/button"
import { useAuth } from "@/lib/auth"

type RailPage = "dashboard" | "details" | "settings"

export function Rail({ current }: { current: RailPage }) {
  const { signOut } = useAuth()

  const links = (
    <>
      <RailLink to="/dashboard" label="Dashboard" current={current === "dashboard"}>
        <LayoutDashboardIcon className="size-5" />
      </RailLink>
      <RailLink to="/details" label="Details" current={current === "details"}>
        <ListIcon className="size-5" />
      </RailLink>
    </>
  )

  const account = (
    <>
      <RailLink to="/settings" label="Settings" current={current === "settings"}>
        <SettingsIcon className="size-5" />
      </RailLink>
      <Button
        variant="ghost"
        size="icon-lg"
        type="button"
        aria-label="Sign out"
        onClick={() => void signOut()}
      >
        <LogOutIcon className="size-5" />
      </Button>
    </>
  )

  return (
    <>
      <nav
        aria-label="Desk"
        className="hidden h-full w-16 shrink-0 flex-col items-center gap-1 border-e bg-card py-3 md:flex"
      >
        <div className="mb-3 flex size-10 items-center justify-center text-foreground">
          <RocketIcon className="size-6" aria-hidden />
          <span className="sr-only">Spaceship</span>
        </div>
        {links}
        <div className="mt-auto flex flex-col items-center gap-1">{account}</div>
      </nav>
      <nav
        aria-label="Desk"
        className="fixed inset-x-0 bottom-0 z-30 flex h-16 items-center justify-around border-t bg-card px-1 md:hidden"
      >
        {links}
        {account}
      </nav>
    </>
  )
}

function RailLink({
  to,
  label,
  current,
  children,
}: {
  to: string
  label: string
  current: boolean
  children: ReactNode
}) {
  return (
    <Button variant="ghost" size="icon-lg" asChild>
      <Link
        to={to}
        aria-label={label}
        aria-current={current ? "page" : undefined}
        className={current ? "bg-accent text-foreground" : undefined}
      >
        {children}
      </Link>
    </Button>
  )
}
