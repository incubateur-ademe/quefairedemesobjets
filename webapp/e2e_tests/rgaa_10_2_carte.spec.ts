import { expect, FrameLocator, Page } from "@playwright/test"
import { test } from "./fixtures"
import {
  clickFirstClickableActeurMarker,
  getIframe,
  mockApiAdresse,
  navigateTo,
  searchCarteAndWaitForActeurs,
  switchToListeMode,
} from "./helpers"

const NEW_WINDOW_SUFFIX = " - nouvelle fenêtre"

async function linksWithoutNewWindowTitle(context: Page | FrameLocator) {
  return context.locator('a[target="_blank"]').evaluateAll(
    (links, suffix) =>
      links.flatMap((link) => {
        const text = (link.textContent ?? "").replace(/\s+/g, " ").trim()
        const title = link.getAttribute("title") ?? ""
        const isSharer = link.closest(".fr-share") !== null
        const repeatsText = title.toLowerCase().startsWith(text.toLowerCase())
        const isValid = title.endsWith(suffix) && (isSharer || repeatsText)
        return isValid ? [] : [`${text} | ${title}`]
      }),
    NEW_WINDOW_SUFFIX,
  )
}

async function expectNewWindowLinksToBeAnnounced(
  context: Page | FrameLocator,
  minimumCount = 1,
) {
  expect(await context.locator('a[target="_blank"]').count()).toBeGreaterThanOrEqual(
    minimumCount,
  )
  expect(await linksWithoutNewWindowTitle(context)).toEqual([])
}

test.describe("♿ RGAA 10.2 — Liens de la carte ouvrant une nouvelle fenêtre", () => {
  test("Carte, fiche d'un lieu et mode liste : le title reprend l'intitulé et la mention nouvelle fenêtre", async ({
    page,
  }) => {
    await mockApiAdresse(page)
    await navigateTo(page, "/carte")
    await searchCarteAndWaitForActeurs(page, "auray")
    await expectNewWindowLinksToBeAnnounced(page)

    for (const name of ["economie.gouv", "Chambre des Métiers et de l’Artisanat"]) {
      await expect(page.locator("a", { hasText: name }).first()).toHaveAttribute(
        "title",
        `${name}${NEW_WINDOW_SUFFIX}`,
      )
    }

    await clickFirstClickableActeurMarker(page)
    await expect(
      page.locator("#acteurDetailsPanel a[target='_blank']").first(),
    ).toBeAttached()
    await expectNewWindowLinksToBeAnnounced(page, 4)
    await expect(
      page.locator("#acteurDetailsPanel").getByRole("link", { name: "Itinéraire" }),
    ).toHaveAttribute("title", `Itinéraire${NEW_WINDOW_SUFFIX}`)

    await page.getByTestId("acteur-details-close").click()
    await switchToListeMode(page)
    await expect(
      page.getByRole("link", { name: /Proposer un nouveau lieu|Proposer une adresse/ }),
    ).toHaveAttribute("title", /nouvelle fenêtre$/)
    await expectNewWindowLinksToBeAnnounced(page)
  })

  test("Formulaire intégré en iframe : liens du pied de page", async ({ page }) => {
    await navigateTo(page, "/lookbook/preview/iframe/formulaire/")
    const iframe = getIframe(page)
    await expect(
      iframe.getByRole("link", { name: "Réutiliser cette carte sur mon site" }),
    ).toHaveAttribute(
      "title",
      `Réutiliser cette carte sur mon site${NEW_WINDOW_SUFFIX}`,
    )
    await expectNewWindowLinksToBeAnnounced(iframe, 3)
  })

  test("Modale d'intégration", async ({ page }) => {
    await navigateTo(page, "/lookbook/preview/modals/integration/")
    await expectNewWindowLinksToBeAnnounced(page)
  })

  test("Filtre Répar'Acteurs", async ({ page }) => {
    await navigateTo(page, "/lookbook/preview/filtres/label_reparacteurs/")
    await expectNewWindowLinksToBeAnnounced(page)
  })
})
