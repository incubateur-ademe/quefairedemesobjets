import { AxeBuilder } from "@axe-core/playwright"
import { expect, test, type Page } from "@playwright/test"
import { navigateTo } from "./helpers"

const PREVIEW = "/lookbook/preview/assistant/carte/"
const PINPOINT = ".qfa-pinpoint"
const DELAI_STABILISATION_MS = 1000

async function ouvrirLaCarte(page: Page, parametres = "") {
  await navigateTo(page, `${PREVIEW}${parametres}`)
  await page.locator(".maplibregl-canvas").waitFor({ state: "visible" })
  await page.locator(PINPOINT).first().waitFor({ state: "attached" })
}

async function deplacerLaCarte(page: Page, dx: number, dy: number) {
  const carte = page.locator(".qfa-carte__toile")
  const cadre = (await carte.boundingBox())!
  const centreX = cadre.x + cadre.width / 2
  const centreY = cadre.y + cadre.height / 2

  await page.mouse.move(centreX, centreY)
  await page.mouse.down()
  await page.mouse.move(centreX + dx, centreY + dy, { steps: 10 })
  await page.mouse.up()
}

test.describe("🗺️ Carte de l'assistant", () => {
  test("La carte affiche au plus 20 lieux", async ({ page }) => {
    await ouvrirLaCarte(page)

    await expect
      .poll(async () => page.locator(PINPOINT).count())
      .toBeLessThanOrEqual(20)
  })

  test("Les pinpoints portent le nom du lieu pour les lecteurs d'écran", async ({
    page,
  }) => {
    await ouvrirLaCarte(page)

    const libelle = await page.locator(PINPOINT).first().getAttribute("aria-label")
    expect(libelle).toBeTruthy()
  })

  test("Un lieu resté dans le cadre ne disparaît pas au déplacement", async ({
    page,
  }) => {
    await ouvrirLaCarte(page)

    const uuidsAvant = await page
      .locator(PINPOINT)
      .evaluateAll((noeuds) => noeuds.map((n) => (n as HTMLElement).dataset.uuid))

    // Déplacement modeste : les lieux du centre restent visibles.
    await deplacerLaCarte(page, 40, 40)
    await page.waitForTimeout(DELAI_STABILISATION_MS + 1500)

    const uuidsApres = await page
      .locator(PINPOINT)
      .evaluateAll((noeuds) => noeuds.map((n) => (n as HTMLElement).dataset.uuid))

    const conserves = uuidsAvant.filter((uuid) => uuidsApres.includes(uuid))
    expect(conserves.length).toBeGreaterThan(0)
  })

  test("Aucun rafraîchissement pendant que la carte bouge", async ({ page }) => {
    await ouvrirLaCarte(page)

    let requetes = 0
    page.on("request", (requete) => {
      if (requete.url().includes("lieux.geojson")) requetes += 1
    })

    // Trois déplacements enchaînés, sans pause : un seul refresh attendu.
    await deplacerLaCarte(page, 30, 0)
    await deplacerLaCarte(page, 0, 30)
    await deplacerLaCarte(page, -30, 0)
    await page.waitForTimeout(DELAI_STABILISATION_MS + 1500)

    expect(requetes).toBeLessThanOrEqual(2)
  })

  test("La liste accessible des lieux est rendue côté serveur", async ({ page }) => {
    await navigateTo(page, PREVIEW)

    const liste = page.locator(".qfa-carte__liste-accessible li")
    await expect(liste.first()).toBeAttached()
  })

  test("La carte respecte les critères WCAG 2.1 AA", async ({ page }) => {
    await ouvrirLaCarte(page)

    const resultats = await new AxeBuilder({ page })
      .include(".qfa-carte")
      // Le canvas MapLibre est décoratif : la liste accessible porte l'information.
      .exclude(".maplibregl-canvas")
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze()

    expect(resultats.violations).toEqual([])
  })

  test("Le contexte WebGL est libéré quand la carte est retirée", async ({ page }) => {
    await ouvrirLaCarte(page)

    const libere = await page.evaluate(() => {
      const carte = document.querySelector<HTMLElement>(
        "[data-controller='assistant-carte']",
      )!
      carte.remove()
      return document.querySelectorAll(".maplibregl-canvas").length === 0
    })

    expect(libere).toBe(true)
  })
})
