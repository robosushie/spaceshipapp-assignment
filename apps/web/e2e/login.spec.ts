import { expect, test } from "@playwright/test"

test("sign in reaches the desk", async ({ page }) => {
  const email = process.env.BOOTSTRAP_ADMIN_EMAIL
  const password = process.env.BOOTSTRAP_ADMIN_PASSWORD
  test.skip(!email || !password, "Set BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD")
  await page.goto("/login")
  await page.getByLabel("Email").fill(email ?? "")
  await page.getByLabel("Password").fill(password ?? "")
  await page.getByRole("button", { name: "Sign in" }).click()
  await expect(page.getByRole("heading", { name: "Spaceship" })).toBeVisible()
})
