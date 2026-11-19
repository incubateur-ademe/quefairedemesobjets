import { test, expect, FrameLocator, Page } from "@playwright/test"
import { getIframe, navigateTo, TIMEOUT } from "./helpers"

async function expectCarteStructure(context: Page | FrameLocator) {
  const mains = context.getByRole("main")
  await expect(mains).toHaveCount(1)
  await expect(context.locator("main#content")).toBeAttached()

  const banner = context.locator('header[role="banner"]')
  await expect(banner).toHaveCount(1)
  await expect(mains.locator('header[role="banner"]')).toHaveCount(0)
  await expect(banner.locator("xpath=following::main[@id='content']")).toHaveCount(1)

  const nav = banner.getByRole("navigation", { name: "Mode d'affichage" })
  await expect(nav).toHaveCount(1)
  await expect(banner.locator('nav[data-testid="view-mode-nav"]')).toHaveCount(1)
}

test.describe("♿ RGAA 9.2 — Structure du document de la carte", () => {
  test("La carte en page directe a un header avant le main et un nav", async ({
    page,
  }) => {
    await navigateTo(page, "/carte")
    await expectCarteStructure(page)
  })

  test("La carte en iframe a un header avant le main et un nav", async ({ page }) => {
    await navigateTo(page, "/robots.txt")
    await page.evaluate(() => {
      const frame = document.createElement("iframe")
      frame.id = "carte"
      frame.src = "/carte"
      document.body.appendChild(frame)
    })
    const iframe = getIframe(page, "carte")
    await expect(iframe.locator("body")).toBeAttached({ timeout: TIMEOUT.DEFAULT })
    await expectCarteStructure(iframe)
  })
})
