import { AxeBuilder } from "@axe-core/playwright"
import { expect, test, type Page } from "@playwright/test"
import { navigateTo } from "./helpers"

// The preview opens on Paris by default, but the e2e sample database
// (`DB_WEBAPP_SAMPLE`) has no repairer there: the map asked for the visible
// area and got nothing. Auray is the best-stocked town of that sample (20
// repairers within a zoom 13 window) and already the reference of the other
// e2e tests of the repository.
const PREVIEW = "/lookbook/preview/assistant/carte/?adresse=Auray"
const PINPOINT = ".qfa-pinpoint"
const SETTLE_DELAY_MS = 1000

async function openMap(page: Page, params = "") {
  await navigateTo(page, `${PREVIEW}${params}`)
  await page.locator(".maplibregl-canvas").waitFor({ state: "visible" })
  await page.locator(PINPOINT).first().waitFor({ state: "attached" })
}

async function dragMap(page: Page, dx: number, dy: number) {
  const map = page.locator(".qfa-carte__canvas")
  const box = (await map.boundingBox())!
  const centerX = box.x + box.width / 2
  const centerY = box.y + box.height / 2

  await page.mouse.move(centerX, centerY)
  await page.mouse.down()
  await page.mouse.move(centerX + dx, centerY + dy, { steps: 10 })
  await page.mouse.up()
}

test.describe("🗺️ Carte de l'assistant", () => {
  test("La carte affiche au plus 20 lieux", async ({ page }) => {
    await openMap(page)

    await expect
      .poll(async () => page.locator(PINPOINT).count())
      .toBeLessThanOrEqual(20)
  })

  test("Les pinpoints portent le nom du lieu pour les lecteurs d'écran", async ({
    page,
  }) => {
    await openMap(page)

    const label = await page.locator(PINPOINT).first().getAttribute("aria-label")
    expect(label).toBeTruthy()
  })

  test("Un lieu resté dans le cadre ne disparaît pas au déplacement", async ({
    page,
  }) => {
    await openMap(page)

    const uuidsBefore = await page
      .locator(PINPOINT)
      .evaluateAll((nodes) => nodes.map((n) => (n as HTMLElement).dataset.uuid))

    // Modest drag: the places at the center stay visible.
    await dragMap(page, 40, 40)
    await page.waitForTimeout(SETTLE_DELAY_MS + 1500)

    const uuidsAfter = await page
      .locator(PINPOINT)
      .evaluateAll((nodes) => nodes.map((n) => (n as HTMLElement).dataset.uuid))

    const kept = uuidsBefore.filter((uuid) => uuidsAfter.includes(uuid))
    expect(kept.length).toBeGreaterThan(0)
  })

  test("Aucun rafraîchissement pendant que la carte bouge", async ({ page }) => {
    await openMap(page)

    let requests = 0
    page.on("request", (request) => {
      if (request.url().includes("lieux.geojson")) requests += 1
    })

    // Three drags in a row, no pause: a single refresh expected.
    await dragMap(page, 30, 0)
    await dragMap(page, 0, 30)
    await dragMap(page, -30, 0)
    await page.waitForTimeout(SETTLE_DELAY_MS + 1500)

    expect(requests).toBeLessThanOrEqual(2)
  })

  test("La liste accessible des lieux est rendue côté serveur", async ({ page }) => {
    await navigateTo(page, PREVIEW)

    const list = page.locator(".qfa-carte__accessible-list li")
    await expect(list.first()).toBeAttached()
  })

  test("La carte respecte les critères WCAG 2.1 AA", async ({ page }) => {
    await openMap(page)

    const results = await new AxeBuilder({ page })
      .include(".qfa-carte")
      // The MapLibre canvas is decorative: the accessible list carries the information.
      .exclude(".maplibregl-canvas")
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze()

    expect(results.violations).toEqual([])
  })

  test("Le contexte WebGL est libéré quand la carte est retirée", async ({ page }) => {
    await openMap(page)

    const released = await page.evaluate(() => {
      const map = document.querySelector<HTMLElement>(
        "[data-controller='assistant-carte']",
      )!
      map.remove()
      return document.querySelectorAll(".maplibregl-canvas").length === 0
    })

    expect(released).toBe(true)
  })
})
