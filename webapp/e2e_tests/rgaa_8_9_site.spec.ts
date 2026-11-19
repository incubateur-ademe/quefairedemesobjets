import { test, expect } from "@playwright/test"
import { navigateTo } from "./helpers"

test.describe("♿ RGAA 8.9 — Balises non utilisées à des fins de présentation", () => {
  test("Accueil : un badge seul n'est pas dans une liste", async ({ page }) => {
    await navigateTo(page, "/")

    const groups = page.locator(".fr-card__header .fr-badges-group")
    expect(await groups.count()).toBeGreaterThan(0)

    const singleItemLists = await page
      .locator("ul.fr-badges-group")
      .evaluateAll(
        (lists) =>
          lists.filter((list) => list.querySelectorAll(":scope > li").length < 2)
            .length,
      )
    expect(singleItemLists).toBe(0)

    await expect(
      page.locator(".fr-card__header .fr-badges-group:not(ul) > p.fr-badge").first(),
    ).toBeVisible()
  })

  test("Fiche produit : les textes des sections sont dans des paragraphes", async ({
    page,
  }) => {
    await navigateTo(page, "/dechet/vaisselle-jetable/")

    for (const title of ["Que va-t-il devenir ?", "Comment consommer responsable ?"]) {
      const content = page.locator(`div[id="${title}"] > div`)
      await expect(content).toHaveCount(1)
      const looseText = await content.evaluate(
        (el) =>
          Array.from(el.childNodes).filter(
            (node) =>
              (node.nodeType === Node.TEXT_NODE && node.textContent?.trim()) ||
              (node instanceof HTMLElement && node.tagName === "BR"),
          ).length,
      )
      expect(looseText, title).toBe(0)
      expect(await content.locator("> p").count(), title).toBeGreaterThan(0)
    }
  })
})
