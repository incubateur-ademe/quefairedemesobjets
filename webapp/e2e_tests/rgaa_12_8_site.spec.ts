import { test, expect, Page } from "@playwright/test"
import { navigateTo } from "./helpers"

const MAX_TAB_STOPS = 80
const SHARE_BUTTON_TESTID = "modal-button-partager-le-site"
// Inline elements on the same line (superscript, icons) can sit a few pixels apart.
const SAME_LINE_TOLERANCE = 8

const pages = [
  {
    name: "Déchets alimentaires",
    path: "/categories/biodechets/dechets-alimentaires/",
  },
  {
    name: "Téléphone mobile (page de destination de l'ancienne fiche)",
    path: "/dechet/telephone-mobile/",
  },
]

const viewports = [
  { width: 1440, height: 900, nextStop: "infotri-link" },
  { width: 390, height: 844, nextStop: "Nouvelle recherche" },
]

async function focusLastBreadcrumbLink(page: Page) {
  const toggle = page.getByRole("button", { name: "Voir le fil d’Ariane" })
  if (await toggle.isVisible()) {
    await toggle.click()
    await expect(page.locator("#page-breadcrumb")).toHaveClass(/fr-collapse--expanded/)
    // DSFR moves focus to the first link on expand and checks it on the next frames.
    await expect(page.locator(".fr-breadcrumb__link").first()).toBeFocused()
    await page.evaluate(
      () =>
        new Promise((resolve) =>
          requestAnimationFrame(() => requestAnimationFrame(resolve)),
        ),
    )
  }
  await page.locator(".fr-breadcrumb__link").last().focus()
}

async function describeFocus(page: Page) {
  return page.evaluate(() => {
    const element = document.activeElement as HTMLElement
    return {
      testId: element.getAttribute("data-testid"),
      text: element.textContent?.trim(),
      top: element.getBoundingClientRect().top + window.scrollY,
    }
  })
}

test.describe("♿ RGAA 12.8 — Ordre de tabulation cohérent (site)", () => {
  for (const { name, path } of pages) {
    test(`${name} : l'ordre de tabulation suit l'ordre visuel`, async ({ page }) => {
      for (const viewport of viewports) {
        await page.setViewportSize(viewport)
        await navigateTo(page, path)
        await focusLastBreadcrumbLink(page)
        const breadcrumb = await describeFocus(page)

        await page.keyboard.press("Tab")
        const next = await describeFocus(page)
        expect(next.testId ?? next.text, `${viewport.width}px`).toBe(viewport.nextStop)

        let previousTop = breadcrumb.top
        let reachedShare = false
        for (let stop = 0; stop < MAX_TAB_STOPS; stop++) {
          const current = await describeFocus(page)
          expect(
            current.top,
            `${viewport.width}px, arrêt ${stop} : retour en arrière visuel`,
          ).toBeGreaterThanOrEqual(previousTop - SAME_LINE_TOLERANCE)
          previousTop = current.top
          if (current.testId === SHARE_BUTTON_TESTID) {
            reachedShare = true
            break
          }
          await page.keyboard.press("Tab")
        }
        expect(reachedShare, `${viewport.width}px`).toBe(true)

        const shareTop = (await describeFocus(page)).top
        expect(shareTop, `${viewport.width}px`).toBeGreaterThan(next.top)
      }
    })
  }
})
