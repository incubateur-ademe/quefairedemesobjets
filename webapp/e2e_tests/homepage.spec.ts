import { test, expect } from "@playwright/test"
import { navigateTo } from "./helpers"

test.describe("Page d'accueil", () => {
  test("Test screenshots", { tag: ["@regression"] }, async ({ page }) => {
    await navigateTo(page, "/")
    await page.waitForTimeout(5000)
  })
  test(
    "Pas de scrollbar horizontale à 320px de largeur",
    { tag: ["@responsive"] },
    async ({ page }) => {
      await page.setViewportSize({ width: 320, height: 568 })
      await navigateTo(page, `/`)

      const hasHorizontalOverflow = await page.evaluate(
        () =>
          document.documentElement.scrollWidth > document.documentElement.clientWidth,
      )

      expect(hasHorizontalOverflow).toBe(false)
    },
  )
  test("Pas de scrollbar sur la home en iframe sur 600 pixels de haut", async ({
    page,
  }) => {
    await navigateTo(page, "/lookbook/preview/iframe/assistant_600px")
    const iframeAssistant = page.locator(`iframe`)
    const bodyInIframe = iframeAssistant.contentFrame().locator("body")

    const iframeAssistantBb = await iframeAssistant.boundingBox()
    const bodyBb = await bodyInIframe.boundingBox()
    expect(iframeAssistantBb!.height).toBeGreaterThan(bodyBb!.height)
  })
})
