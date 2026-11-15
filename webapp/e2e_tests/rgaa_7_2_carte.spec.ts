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

const NEXT_PAGE = /suivante|next page/i

async function expectTabsFollowKeyboardModel(fiche: Locator, expectedTabs: number) {
  const tabs = fiche.getByRole("tab")
  await expect(tabs).toHaveCount(expectedTabs)

  // Every tabpanel has its tab, and is named by it
  const panels = fiche.getByRole("tabpanel", { includeHidden: true })
  await expect(panels).toHaveCount(expectedTabs)
  const panelNames = await panels.evaluateAll((nodes) =>
    nodes.map((panel) => {
      const labeller = document.getElementById(
        panel.getAttribute("aria-labelledby") ?? "",
      )
      return {
        isTab: labeller?.getAttribute("role") === "tab",
        controlsPanel: labeller?.getAttribute("aria-controls") === panel.id,
      }
    }),
  )
  for (const name of panelNames)
    expect(name).toEqual({ isTab: true, controlsPanel: true })

  // A single selected tab, and the only one in the tab order
  await expect(fiche.locator('[role="tab"][aria-selected="true"]')).toHaveCount(1)
  await expect(fiche.locator('[role="tab"][tabindex="0"]')).toHaveCount(1)
  await expect(tabs.first()).toHaveAttribute("aria-selected", "true")

  // Arrow keys move the focus along with the selection
  await tabs.first().focus()
  await page_press(fiche, "ArrowRight")
  await expect(tabs.nth(1)).toBeFocused()
  await expect(tabs.nth(1)).toHaveAttribute("aria-selected", "true")
  await expect(tabs.nth(1)).toHaveAttribute("tabindex", "0")
  await expect(tabs.first()).toHaveAttribute("tabindex", "-1")
  await page_press(fiche, "End")
  await expect(tabs.last()).toBeFocused()
  await page_press(fiche, "Home")
  await expect(tabs.first()).toBeFocused()
  await expect(tabs.first()).toHaveAttribute("aria-selected", "true")
}

function page_press(fiche: Locator, key: string) {
  return fiche.page().keyboard.press(key)
}

async function openFiche(page: Page, row: Locator) {
  await row.click()
  const fiche = page.locator("#acteurDetailsPanel")
  await expect(fiche.getByTestId("acteur-title")).toBeVisible({
    timeout: TIMEOUT.DEFAULT,
  })
  return fiche
}

async function closeFicheWithEscape(page: Page, fiche: Locator, opener: Locator) {
  await focusEdgeTabbable(fiche, "first")
  await pressTab(page, 3)
  await page.keyboard.press("Escape")
  await expect(fiche).toBeHidden()
  await expect(opener).toBeFocused()
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

    // Listening starts after the search: its overlapping autocomplete requests
    // already raise an unrelated Turbo error.
    const pageErrors: string[] = []
    page.on("pageerror", (error) => pageErrors.push(error.message))
    const liste = page.getByTestId("liste-mode-container")
    const voirLaFiche = liste.getByTestId("voir-la-fiche")

    // Point 3 : Échap ferme la modale Filtres même après avoir tabulé dans ses champs,
    // y compris depuis un champ de saisie, et le focus revient sur le bouton Filtres
    const filtresButton = liste.getByTestId("modal-button-carte:filtres")
    const filtres = page.getByTestId("modal-carte:filtres")
    await filtresButton.click()
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
    await expect(filtresButton).toBeFocused()

    await filtresButton.click()
    await expect(filtres).toBeVisible()
    await filtres.locator('input[id$="_filtres-synonyme"]').focus()
    await page.keyboard.press("Escape")
    await expect(filtres).toBeHidden()
    await expect(filtresButton).toBeFocused()

    // Point 1 : ouvrir la fiche est une action, donc un bouton
    await expect(voirLaFiche.first()).toHaveJSProperty("tagName", "BUTTON")
    await expect(liste.getByTestId("acteur-list-link").first()).toHaveJSProperty(
      "tagName",
      "BUTTON",
    )

    // Un lieu avec labels et un lieu sans labels, choisis dans la page affichée
    const urls = await voirLaFiche.evaluateAll((buttons) =>
      buttons.map((button) => button.getAttribute("data-frame-link-url-value") ?? ""),
    )
    const hasLabelsTab = await Promise.all(
      urls.map(async (url) =>
        (await (await page.request.get(url)).text()).includes("labelsPanelTab"),
      ),
    )
    const withLabels = hasLabelsTab.indexOf(true)
    const withoutLabels = hasLabelsTab.indexOf(false)
    expect(withLabels, "un lieu avec labels dans la liste").toBeGreaterThanOrEqual(0)
    expect(withoutLabels, "un lieu sans labels dans la liste").toBeGreaterThanOrEqual(0)

    // Point 2 : la fiche est une modale <dialog>, le focus y entre et y reste
    const opener = voirLaFiche.nth(withLabels)
    const fiche = await openFiche(page, opener)
    await expect(fiche).toHaveJSProperty("tagName", "DIALOG")
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

    // Point 4 : onglets (lieu avec labels : 3 onglets)
    await expectTabsFollowKeyboardModel(fiche, 3)

    // Point 5 : le partage n'est pas un tooltip, Échap le ferme avant la fiche
    const partager = fiche.getByRole("button", { name: "partager" })
    await expect(partager).not.toHaveAttribute("aria-describedby")
    await partager.click()
    await expect(partager).toHaveAttribute("aria-expanded", "true")
    await expect(fiche.getByRole("link", { name: /Facebook/ })).toBeVisible()
    await page.keyboard.press("Escape")
    await expect(partager).toHaveAttribute("aria-expanded", "false")
    await expect(fiche).toHaveAttribute("open")

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
    await closeFicheWithEscape(page, fiche, opener)

    // Point 4 : lieu sans labels, pas de panneau orphelin (2 onglets, 2 panneaux)
    const ficheWithoutLabels = await openFiche(page, voirLaFiche.nth(withoutLabels))
    await expect(ficheWithoutLabels.getByRole("tab", { name: "Labels" })).toHaveCount(0)
    await expectTabsFollowKeyboardModel(ficheWithoutLabels, 2)
    await closeFicheWithEscape(page, ficheWithoutLabels, voirLaFiche.nth(withoutLabels))

    // Point 7 : la pagination est faite de boutons, charge la page sans changer d'URL
    // et place le focus sur la liste
    const pagination = liste.getByRole("navigation", { name: "Pagination" })
    await expect(pagination.getByRole("button", { name: NEXT_PAGE })).toBeEnabled()
    await expect(pagination.getByRole("link")).toHaveCount(0)
    await expect(pagination.locator("a")).toHaveCount(0)
    const urlBefore = page.url()
    for (let pageNumber = 2; pageNumber <= 4; pageNumber++) {
      await pagination.getByRole("button", { name: NEXT_PAGE }).click()
      await expect(liste).toBeFocused({ timeout: TIMEOUT.DEFAULT })
      await expect(pagination.locator('[aria-current="page"]')).toContainText(
        `${pageNumber}`,
      )
    }
    expect(page.url()).toBe(urlBefore)

    // Après la pagination, ouvrir une fiche ne lève aucune erreur
    const ficheAfterPagination = await openFiche(page, voirLaFiche.first())
    await expect(ficheAfterPagination).toHaveAttribute("open")
    expect(pageErrors).toEqual([])
  })
})
