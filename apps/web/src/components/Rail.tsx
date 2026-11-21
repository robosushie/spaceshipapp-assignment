import { LayoutDashboardIcon, LogOutIcon, RocketIcon, SettingsIcon } from "lucide-react"
import { Link } from "react-router"

import { Button } from "@/components/ui/button"
import { useAuth } from "@/lib/auth"

export function Rail({ current }: { current: "dashboard" | "settings" }) {
  const { signOut } = useAuth()
  const active = "bg-accent text-foreground"

  return (
    <nav
      aria-label="Desk"
      className="flex h-full w-16 shrink-0 flex-col items-center gap-1 border-e bg-card py-3"
    >
      <div className="mb-3 flex size-10 items-center justify-center text-foreground">
        <RocketIcon className="size-6" aria-hidden />
        <span className="sr-only">Spaceship</span>
      </div>
      <Button variant="ghost" size="icon-lg" asChild>
        <Link
          to="/dashboard"
          aria-label="Dashboard"
          aria-current={current === "dashboard" ? "page" : undefined}
          className={current === "dashboard" ? active : undefined}
        >
          <LayoutDashboardIcon className="size-5" />
        </Link>
      </Button>
      <div className="mt-auto flex flex-col items-center gap-1">
        <Button variant="ghost" size="icon-lg" asChild>
          <Link
            to="/settings"
            aria-label="Settings"
            aria-current={current === "settings" ? "page" : undefined}
            className={current === "settings" ? active : undefined}
          >
            <SettingsIcon className="size-5" />
          </Link>
        </Button>
        <Button
          variant="ghost"
          size="icon-lg"
          type="button"
          aria-label="Sign out"
          onClick={() => void signOut()}
        >
          <LogOutIcon className="size-5" />
        </Button>
      </div>
    </nav>
  )
}
