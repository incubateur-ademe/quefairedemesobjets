import { expect, test } from "@playwright/test"
import { navigateTo } from "./helpers"

test.describe("♿ RGAA 9.3 — Listes correctement structurées", () => {
  test("La page Déchets alimentaires expose ses puces emoji en listes", async ({
    page,
  }) => {
    await navigateTo(page, "/categories/biodechets/dechets-alimentaires/")

    const cards = page.locator(".fr-card", { has: page.locator("h3") })
    const lists = [
      ["A mettre au compost", 3],
      ["En petites quantités", 4],
      ["A ne pas composter", 3],
    ] as const

    for (const [title, count] of lists) {
      const card = cards.filter({ hasText: title })
      const list = card.getByRole("list")
      await expect(list).toHaveCount(1)
      await expect(list.getByRole("listitem")).toHaveCount(count)
    }

    const paragraphsAsBullets = page.locator(
      "p.fr-card__desc:is(:has-text('✅'), :has-text('🟠'), :has-text('‼️'))",
    )
    await expect(paragraphsAsBullets).toHaveCount(0)
  })

  test("La page Aspirateur expose ses puces ➡️ en listes", async ({ page }) => {
    await navigateTo(page, "/categories/petit-electromenager/aspirateur/")

    const donner = page
      .locator(".fr-card", {
        has: page.getByRole("heading", { name: "Donner ou revendre" }),
      })
      .locator("ul.fr-card__desc")
    await expect(donner.getByRole("listitem")).toHaveCount(2)

    const deposer = page
      .locator(".fr-card", {
        has: page.getByRole("heading", { name: "Déposer" }),
      })
      .locator("ul.fr-card__desc")
    await expect(deposer.getByRole("listitem")).toHaveCount(2)
  })

  test("La page famille Vêtements expose ses notes de bas de page en liste ordonnée", async ({
    page,
  }) => {
    await navigateTo(page, "/categories/vetements/")

    const notes = page.getByRole("list", { name: "Notes de bas de page" })
    await expect(notes).toHaveCount(1)
    expect(await notes.evaluate((el) => el.tagName)).toBe("OL")
    await expect(notes.getByRole("listitem")).toHaveCount(2)
  })
})
