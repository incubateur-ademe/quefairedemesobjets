import { AxeBuilder } from "@axe-core/playwright"
import { expect, test, type Page } from "@playwright/test"
import { navigateTo } from "./helpers"

// The e2e sample database has no repairer in Paris: Auray is its best stocked.
const PREVIEW = "/lookbook/preview/assistant/carte/?adresse=Auray"
const PINPOINT = ".qfa-pinpoint"

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

// One map opened for the whole spec: what Jest and the Python tests cannot see
// is the real browser, its accessibility and a real drag.
test.describe("🗺️ Carte de l'assistant", () => {
  test("La carte est accessible et garde ses lieux au déplacement", async ({
    page,
  }) => {
    await openMap(page)

    const results = await new AxeBuilder({ page })
      .include(".qfa-carte")
      // The canvas is decorative: the accessible list carries the information.
      .exclude(".maplibregl-canvas")
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze()
    expect(results.violations).toEqual([])

    const uuids = () =>
      page
        .locator(PINPOINT)
        .evaluateAll((nodes) => nodes.map((n) => (n as HTMLElement).dataset.uuid))
    const before = await uuids()

    const refreshed = page.waitForResponse((r) => r.url().includes("lieux.geojson"))
    await dragMap(page, 40, 40)
    await refreshed

    const after = await uuids()
    expect(before.filter((uuid) => after.includes(uuid)).length).toBeGreaterThan(0)
  })
})
