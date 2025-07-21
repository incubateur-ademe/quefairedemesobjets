import { expect } from "@playwright/test"
import { test } from "./config"
import { hideDjangoToolbar } from "./helpers"

test.describe(
  "django-admin",
  {
    tag: ["@djangoadmin"],
  },
  () => {
    test.skip("Django Admin, créer un produit fonctionne", async ({ page }) => {
      await page.goto(`/admin/qfdmd/produit/add/`, { waitUntil: "domcontentloaded" })
      await page.locator("input#id_username").fill("admin")
      await page.locator("input#id_password").fill("admin")
      await page.locator("input[type=submit]").click()
      await page.locator("input#id_id").fill(parseInt(Math.random() * 1000).toString())
      await page.locator("input#id_nom").fill(new Date().toISOString())
      await page.getByRole("button", { name: "Enregistrer", exact: true }).click()
      await expect(page).toHaveURL(/\/produit\/$/)
      await page.waitForEvent("domcontentloaded")

      expect(page.locator(".success")).toContainText("L'objet produit")
    })
  },
)
