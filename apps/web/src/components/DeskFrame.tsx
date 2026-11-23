import { useEffect, useState } from "react"
import { BotIcon } from "lucide-react"
import { Outlet, useLocation } from "react-router"

import { AgentPanel } from "@/components/AgentPanel"
import { Rail } from "@/components/Rail"
import { Button } from "@/components/ui/button"
import { loadChats, saveChats, type ChatDesk } from "@/lib/chats"
import { cn } from "@/lib/utils"

const CHAT_WIDTH_KEY = "spaceship-chat-width"
const CHAT_DEFAULT = 320
const CHAT_MIN = 220
const CHAT_MAX = 720

function clampChatWidth(value: number, viewport: number): number {
  const max = Math.min(CHAT_MAX, Math.round(viewport * 0.7))
  return Math.min(Math.max(value, CHAT_MIN), Math.max(max, CHAT_MIN))
}

function loadChatWidth(): number {
  if (typeof localStorage === "undefined") {
    return CHAT_DEFAULT
  }
  const stored = Number(localStorage.getItem(CHAT_WIDTH_KEY))
  if (!Number.isFinite(stored)) {
    return CHAT_DEFAULT
  }
  return clampChatWidth(stored, window.innerWidth)
}

export function DeskFrame() {
  const { pathname } = useLocation()
  const [open, setOpen] = useState(false)
  const [chatWidth, setChatWidth] = useState(loadChatWidth)
  const [desk, setDesk] = useState<ChatDesk>(loadChats)
  const current = pathname.startsWith("/details") ? "details" : "dashboard"

  useEffect(() => {
    saveChats(desk)
  }, [desk])

  useEffect(() => {
    localStorage.setItem(CHAT_WIDTH_KEY, String(chatWidth))
  }, [chatWidth])

  useEffect(() => {
    if (!open) {
      return
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false)
      }
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [open])

  function toggle() {
    setOpen((currentOpen) => !currentOpen)
  }

  return (
    <div className="flex h-svh overflow-hidden">
      <Rail
        current={current}
        agent={<AgentButton open={open} onClick={toggle} className="flex-col gap-0.5" />}
      />
      <div className="min-h-0 min-w-0 flex-1 pb-16 md:pb-0">
        <Outlet />
      </div>
      <AgentButton
        open={open}
        onClick={toggle}
        className="fixed bottom-2 left-1 z-40 hidden w-14 flex-col gap-0.5 md:inline-flex"
      />
      {open ? (
        <AgentPanel
          width={chatWidth}
          onWidth={setChatWidth}
          onClose={() => setOpen(false)}
          desk={desk}
          setDesk={setDesk}
        />
      ) : null}
    </div>
  )
}

function AgentButton({
  open,
  onClick,
  className,
}: {
  open: boolean
  onClick: () => void
  className?: string
}) {
  return (
    <Button
      type="button"
      variant={open ? "secondary" : "ghost"}
      aria-expanded={open}
      aria-controls="agent-panel"
      onClick={onClick}
      className={cn("h-auto px-1 py-1 text-[11px] leading-none", className)}
    >
      <BotIcon className="size-5" />
      Agent
    </Button>
  )
}
