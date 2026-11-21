import { useEffect, useState, type FormEvent } from "react"

import { Rail } from "@/components/Rail"
import { Button } from "@/components/ui/button"
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ApiError, api } from "@/lib/api"

type Role = "admin" | "member"

type Profile = {
  id: number
  email: string
  name: string
  role: Role
}

export function Settings() {
  const [profile, setProfile] = useState<Profile | null>(null)
  const [name, setName] = useState("")
  const [role, setRole] = useState<Role>("member")
  const [profileError, setProfileError] = useState<string | null>(null)
  const [profileNotice, setProfileNotice] = useState<string | null>(null)
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [passwordNotice, setPasswordNotice] = useState<string | null>(null)
  const [inviteName, setInviteName] = useState("")
  const [inviteEmail, setInviteEmail] = useState("")
  const [inviteRole, setInviteRole] = useState<Role>("member")
  const [inviteError, setInviteError] = useState<string | null>(null)
  const [inviteNotice, setInviteNotice] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    api<Profile>("/v1/me")
      .then((body) => {
        if (cancelled) return
        setProfile(body)
        setName(body.name)
        setRole(body.role)
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setProfileError(caught instanceof ApiError ? caught.message : "Profile could not be loaded.")
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

  async function saveProfile(event: FormEvent) {
    event.preventDefault()
    setProfileError(null)
    setProfileNotice(null)
    try {
      const body = await api<Profile>("/v1/me", {
        method: "POST",
        body: JSON.stringify({ name, role }),
      })
      setProfile(body)
      setName(body.name)
      setRole(body.role)
      setProfileNotice("Profile saved.")
    } catch (caught) {
      setProfileError(caught instanceof ApiError ? caught.message : "Profile could not be saved.")
    }
  }

  async function savePassword(event: FormEvent) {
    event.preventDefault()
    setPasswordError(null)
    setPasswordNotice(null)
    try {
      await api<void>("/v1/me/password", {
        method: "POST",
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      })
      setCurrentPassword("")
      setNewPassword("")
      setPasswordNotice("Password updated.")
    } catch (caught) {
      setPasswordError(caught instanceof ApiError ? caught.message : "Password could not be updated.")
    }
  }

  async function sendInvite(event: FormEvent) {
    event.preventDefault()
    setInviteError(null)
    setInviteNotice(null)
    try {
      const body = await api<{ email: string }>("/v1/invites", {
        method: "POST",
        body: JSON.stringify({ name: inviteName, email: inviteEmail, role: inviteRole }),
      })
      setInviteName("")
      setInviteEmail("")
      setInviteRole("member")
      setInviteNotice(`Invite sent to ${body.email}.`)
    } catch (caught) {
      setInviteError(caught instanceof ApiError ? caught.message : "Invite could not be sent.")
    }
  }

  return (
    <div className="flex h-svh overflow-hidden">
    <Rail current="settings" />
    <main className="min-h-0 flex-1 overflow-y-auto">
    <div className="mx-auto flex max-w-lg flex-col gap-8 px-6 py-8">
      <h1 className="text-[28px] leading-[1.14] tracking-[-0.022em]">Settings</h1>
      {profile === null && profileError === null ? (
        <p className="text-sm text-muted-foreground">Loading profile.</p>
      ) : null}
      {profileError && profile === null ? <p className="text-sm text-primary">{profileError}</p> : null}
      {profile ? (
        <Tabs defaultValue="profile">
          <TabsList>
            <TabsTrigger value="profile">Profile</TabsTrigger>
            {profile.role === "admin" ? <TabsTrigger value="invite">Invite</TabsTrigger> : null}
          </TabsList>
          <TabsContent value="profile" className="flex flex-col gap-10 pt-4">
            <form onSubmit={(event) => void saveProfile(event)}>
              <FieldGroup>
                <Field>
                  <FieldLabel htmlFor="name">Name</FieldLabel>
                  <Input id="name" required value={name} onChange={(event) => setName(event.target.value)} />
                </Field>
                <Field>
                  <FieldLabel htmlFor="role">Role</FieldLabel>
                  <Select value={role} onValueChange={(value) => setRole(value as Role)}>
                    <SelectTrigger id="role" className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="member">Member</SelectItem>
                      <SelectItem value="admin">Admin</SelectItem>
                    </SelectContent>
                  </Select>
                </Field>
                <Field>
                  <FieldLabel htmlFor="email">Email</FieldLabel>
                  <Input id="email" value={profile.email} readOnly />
                </Field>
                {profileError ? <FieldError>{profileError}</FieldError> : null}
                {profileNotice ? <p className="text-sm text-muted-foreground">{profileNotice}</p> : null}
                <Button type="submit">Save profile</Button>
              </FieldGroup>
            </form>
            <form onSubmit={(event) => void savePassword(event)}>
              <FieldGroup>
                <Field data-invalid={passwordError ? true : undefined}>
                  <FieldLabel htmlFor="current-password">Current password</FieldLabel>
                  <Input
                    id="current-password"
                    type="password"
                    autoComplete="current-password"
                    required
                    value={currentPassword}
                    onChange={(event) => setCurrentPassword(event.target.value)}
                  />
                </Field>
                <Field data-invalid={passwordError ? true : undefined}>
                  <FieldLabel htmlFor="new-password">New password</FieldLabel>
                  <Input
                    id="new-password"
                    type="password"
                    autoComplete="new-password"
                    required
                    minLength={8}
                    value={newPassword}
                    onChange={(event) => setNewPassword(event.target.value)}
                  />
                  {passwordError ? <FieldError>{passwordError}</FieldError> : null}
                  {passwordNotice ? <p className="text-sm text-muted-foreground">{passwordNotice}</p> : null}
                </Field>
                <Button type="submit">Change password</Button>
              </FieldGroup>
            </form>
          </TabsContent>
          {profile.role === "admin" ? (
            <TabsContent value="invite" className="pt-4">
              <form onSubmit={(event) => void sendInvite(event)}>
                <FieldGroup>
                  <Field>
                    <FieldLabel htmlFor="invite-name">Name</FieldLabel>
                    <Input
                      id="invite-name"
                      required
                      value={inviteName}
                      onChange={(event) => setInviteName(event.target.value)}
                    />
                  </Field>
                  <Field>
                    <FieldLabel htmlFor="invite-email">Email</FieldLabel>
                    <Input
                      id="invite-email"
                      type="email"
                      required
                      value={inviteEmail}
                      onChange={(event) => setInviteEmail(event.target.value)}
                    />
                  </Field>
                  <Field>
                    <FieldLabel htmlFor="invite-role">Role</FieldLabel>
                    <Select value={inviteRole} onValueChange={(value) => setInviteRole(value as Role)}>
                      <SelectTrigger id="invite-role" className="w-full">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="member">Member</SelectItem>
                        <SelectItem value="admin">Admin</SelectItem>
                      </SelectContent>
                    </Select>
                  </Field>
                  <p className="text-sm text-muted-foreground">
                    Until a sending domain is verified, mail from onboarding@resend.dev only arrives at the
                    address on the Resend account.
                  </p>
                  {inviteError ? <FieldError>{inviteError}</FieldError> : null}
                  {inviteNotice ? <p className="text-sm text-muted-foreground">{inviteNotice}</p> : null}
                  <Button type="submit">Send invite</Button>
                </FieldGroup>
              </form>
            </TabsContent>
          ) : null}
        </Tabs>
      ) : null}
    </div>
    </main>
    </div>
  )
}
