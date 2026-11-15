import { test, expect, Page } from "@playwright/test"
import { navigateTo } from "./helpers"

const headingLevels = (page: Page, scope: string) =>
  page.evaluate(
    (selector) =>
      [...document.querySelectorAll(`${selector} :is(h1,h2,h3,h4,h5,h6)`)].map(
        (heading) => Number(heading.tagName[1]),
      ),
    scope,
  )

const tagName = (page: Page, selector: string) =>
  page.locator(selector).evaluate((element) => element.tagName)

test.describe("♿ RGAA 9.1 — Structuration de l'information par des titres", () => {
  test("Accueil : les tuiles sont des éléments de liste et « Plan du site » est un titre de niveau 2", async ({
    page,
  }) => {
    await navigateTo(page, "/")

    for (const text of [
      "Accéder aux recommandations de tri adaptées à chaque situation",
      "Trouver des lieux proches de chez vous grâce à une carte interactive",
      "S'informer sur le devenir de votre déchet ou de votre objet",
      "Limiter votre impact grâce à une consommation plus responsable",
    ]) {
      await expect(page.getByRole("listitem").filter({ hasText: text })).toHaveCount(1)
      await expect(page.getByRole("heading", { name: text })).toHaveCount(0)
    }

    await expect(page.locator("footer h2", { hasText: "Plan du site" })).toHaveCount(1)
    await expect(page.locator("footer h3", { hasText: "Plan du site" })).toHaveCount(0)
  })

  test("Déclaration d'accessibilité : les titres d'accordéon sont de niveau 2 et leur contenu en dépend", async ({
    page,
  }) => {
    await navigateTo(page, "/accessibilite/")

    const levels = await headingLevels(page, "main")
    const accordionTitles = await page
      .locator("main .fr-accordion__title")
      .evaluateAll((titles) => titles.map((title) => title.tagName))

    expect(accordionTitles).toEqual(["H2", "H2"])
    expect(levels[0]).toBe(1)
    levels.slice(1).forEach((level, index) => {
      expect(level, `saut de niveau avant le titre n°${index + 2}`).toBeLessThanOrEqual(
        levels[index] + 1,
      )
    })
    expect(levels.slice(1, 6)).toEqual([2, 3, 4, 3, 4])
  })

  test("Fiche déchet : les titres des modales Partager et Intégrer sont de niveau 1", async ({
    page,
  }) => {
    await navigateTo(page, "/dechet/dechets-alimentaires")

    expect(await tagName(page, "#fr-modal-partager-le-site .fr-modal__title")).toBe(
      "H1",
    )
    expect(await tagName(page, "#fr-modal-integrer-le-site .fr-modal__title")).toBe(
      "H1",
    )
  })
})
