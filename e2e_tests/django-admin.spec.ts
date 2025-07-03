import { expect } from "@playwright/test"
import { test } from "./config"
import { hideDjangoToolbar } from "./helpers"

test.describe(
  "django-admin",
  {
    tag: ["@djangoadmin"],
  },
  () => {
    test("Django Admin, créer un produit fonctionne", async ({ page }) => {
      await page.goto(`/admin/qfdmd/produit/add/`, { waitUntil: "domcontentloaded" })
      await page.locator("input#id_username").fill("admin")
      await page.locator("input#id_password").fill("admin")
      await page.locator("input[type=submit]").click()
      await page.locator("input#id_id").fill("666")
      await page.locator("input#id_nom").fill("coucou")
      await page.getByRole("button", { name: "Enregistrer", exact: true }).click()
      await page.waitForURL("**\/produit/", { waitUntil: "domcontentloaded" })

      expect(page.locator(".success")).toContainText("L'objet produit")
    })
  },
)
