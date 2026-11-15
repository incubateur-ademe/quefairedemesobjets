import { expect, Locator, Page } from "@playwright/test"
import { test } from "./fixtures"
import {
  mockApiAdresse,
  navigateTo,
  searchCarteAndWaitForActeurs,
  switchToListeMode,
  TIMEOUT,
} from "./helpers"

const TABBABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select, textarea, summary, [tabindex]:not([tabindex="-1"])'

async function isFocusInside(container: Locator) {
  return container.evaluate((el) => el.contains(document.activeElement))
}

async function focusEdgeTabbable(container: Locator, edge: "first" | "last") {
  await container.evaluate(
    (el, { edge, selector }) => {
      const tabbables = [...el.querySelectorAll<HTMLElement>(selector)].filter(
        (node) =>
          node.checkVisibility({ checkVisibilityCSS: true }) && node.tabIndex >= 0,
      )
      tabbables[edge === "first" ? 0 : tabbables.length - 1].focus()
    },
    { edge, selector: TABBABLE },
  )
}

async function activeIsEdgeTabbable(container: Locator, edge: "first" | "last") {
  return container.evaluate(
    (el, { edge, selector }) => {
      const tabbables = [...el.querySelectorAll<HTMLElement>(selector)].filter(
        (node) =>
          node.checkVisibility({ checkVisibilityCSS: true }) && node.tabIndex >= 0,
      )
      return (
        tabbables[edge === "first" ? 0 : tabbables.length - 1] ===
        document.activeElement
      )
    },
    { edge, selector: TABBABLE },
  )
}

async function pressTab(page: Page, times: number) {
  for (let i = 0; i < times; i++) await page.keyboard.press("Tab")
}

test.describe("♿ RGAA 7.2 — Carte, alternative en mode liste", () => {
  test("Le mode liste, la modale Filtres et la fiche lieu sont utilisables au clavier et au lecteur d'écran", async ({
    page,
  }) => {
    test.slow()
    await mockApiAdresse(page)
    await navigateTo(page, "/carte")
    await searchCarteAndWaitForActeurs(page, "auray")
    await switchToListeMode(page)
    const liste = page.getByTestId("liste-mode-container")

    // Point 7 : la pagination est faite de boutons, pas de liens sans destination
    const pagination = liste.getByRole("navigation", { name: "Pagination" })
    await expect(
      pagination.getByRole("button", { name: /suivante|next page/i }),
    ).toBeEnabled()
    await expect(pagination.getByRole("link")).toHaveCount(0)
    await expect(pagination.locator("a")).toHaveCount(0)

    // Point 3 : Échap ferme la modale Filtres même après avoir tabulé dans ses champs
    await liste.getByTestId("modal-button-carte:filtres").click()
    const filtres = page.getByTestId("modal-carte:filtres")
    await expect(filtres).toBeVisible()
    for (let i = 0; i < 10; i++) {
      await page.keyboard.press("Tab")
      const onCheckbox = await page.evaluate(
        () => (document.activeElement as HTMLInputElement | null)?.type === "checkbox",
      )
      if (onCheckbox) break
    }
    expect(await isFocusInside(filtres)).toBe(true)
    await page.keyboard.press("Escape")
    await expect(filtres).toBeHidden()

    // Point 1 : ouvrir la fiche est une action, donc un bouton
    const voirLaFiche = liste.getByTestId("voir-la-fiche").first()
    await expect(voirLaFiche).toHaveJSProperty("tagName", "BUTTON")
    await expect(liste.getByTestId("acteur-list-link").first()).toHaveJSProperty(
      "tagName",
      "BUTTON",
    )

    // Point 2 : la fiche est une modale <dialog>, le focus y entre et y reste
    await voirLaFiche.click()
    const fiche = page.locator("#acteurDetailsPanel")
    await expect(fiche).toHaveJSProperty("tagName", "DIALOG")
    await expect(fiche.getByTestId("acteur-title")).toBeVisible({
      timeout: TIMEOUT.DEFAULT,
    })
    expect(await fiche.evaluate((el) => el.matches(":modal"))).toBe(true)
    await expect(fiche).not.toHaveAttribute("aria-expanded")
    const title = (await fiche.getByTestId("acteur-title").textContent())?.trim() ?? ""
    expect(title).not.toBe("")
    await expect(fiche).toHaveAccessibleName(title)
    expect(await isFocusInside(fiche)).toBe(true)

    await focusEdgeTabbable(fiche, "last")
    await page.keyboard.press("Tab")
    expect(await activeIsEdgeTabbable(fiche, "first")).toBe(true)
    await page.keyboard.press("Shift+Tab")
    expect(await activeIsEdgeTabbable(fiche, "last")).toBe(true)

    // Point 4 : chaque tabpanel est nommé par son onglet
    const panels = fiche.getByRole("tabpanel", { includeHidden: true })
    expect(await panels.count()).toBeGreaterThan(0)
    const tabpanelLabels = await panels.evaluateAll((nodes) =>
      nodes.map((panel) => {
        const labelledBy = panel.getAttribute("aria-labelledby") ?? ""
        const labeller = document.getElementById(labelledBy)
        return {
          labelledBy,
          isTab: labeller?.getAttribute("role") === "tab",
          controlsPanel: labeller?.getAttribute("aria-controls") === panel.id,
        }
      }),
    )
    for (const label of tabpanelLabels) {
      expect(label.isTab, `aria-labelledby=${label.labelledBy}`).toBe(true)
      expect(label.controlsPanel, `aria-labelledby=${label.labelledBy}`).toBe(true)
    }

    // Point 5 : le bouton de partage n'est pas relié à un tooltip
    const partager = fiche.getByRole("button", { name: "partager" })
    await expect(partager).not.toHaveAttribute("aria-describedby")
    await partager.click()
    await expect(fiche.getByRole("link", { name: /Facebook/ })).toBeVisible()

    // Points 6 et 8 : libellés de la carte et du bouton d'information en français
    const canvas = fiche.locator("canvas.maplibregl-canvas")
    await expect(canvas).toBeVisible({ timeout: TIMEOUT.LONG })
    await expect(canvas).toHaveAttribute("aria-label", /^(?!Map$).+/)
    const attribution = fiche.locator(".maplibregl-ctrl-attrib-button")
    await expect(attribution).not.toHaveAttribute("aria-label", "Toggle attribution")
    const attributionLabel = (await attribution.getAttribute("aria-label")) ?? ""
    expect(attributionLabel).not.toBe("")
    await expect(attribution).toHaveAttribute("title", attributionLabel)

    // Point 3 : Échap ferme la fiche après avoir tabulé, le focus revient au bouton
    await focusEdgeTabbable(fiche, "first")
    await pressTab(page, 3)
    await page.keyboard.press("Escape")
    await expect(fiche).toBeHidden()
    await expect(voirLaFiche).toBeFocused()

    // Point 7 : la pagination charge la page suivante sans changer d'URL
    const firstRowName = liste.getByTestId("acteur-list-link").first()
    const firstName = await firstRowName.textContent()
    const urlBefore = page.url()
    await pagination.getByRole("button", { name: /suivante|next page/i }).click()
    await expect(firstRowName).not.toHaveText(firstName ?? "", {
      timeout: TIMEOUT.DEFAULT,
    })
    expect(page.url()).toBe(urlBefore)
  })
})
