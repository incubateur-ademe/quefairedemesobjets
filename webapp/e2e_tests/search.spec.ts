import { expect, test } from "@playwright/test"
import {
  navigateTo,
  SEARCH_INPUT_SELECTOR,
  SEARCH_RESULTS_DROPDOWN_SELECTOR,
  SEARCH_RESULTS_SELECTOR,
  TIMEOUT,
  typeSearchQuery,
  waitForResults,
} from "./helpers"

test.describe("Recherche de produits", () => {
  test.beforeEach(async ({ page }) => {
    await navigateTo(page, "/")
  })

  test("La recherche affiche des résultats pertinents", async ({ page }) => {
    await typeSearchQuery(page, "lave")
    const results = await waitForResults(page)

    const count = await results.count()
    expect(count).toBeGreaterThan(0)
    expect(count).toBeLessThanOrEqual(10)

    // Les premiers résultats doivent contenir le terme recherché
    // ou être sémantiquement liés
    const firstResultText = await results.first().textContent()
    expect(firstResultText).toBeTruthy()
  })

  test("La recherche avec accents retourne des résultats", async ({ page }) => {
    await typeSearchQuery(page, "télé")
    const results = await waitForResults(page)

    const count = await results.count()
    expect(count).toBeGreaterThan(0)
    expect(count).toBeLessThanOrEqual(10)
  })

  test("Les résultats sont des liens cliquables", async ({ page }) => {
    await typeSearchQuery(page, "chaise")
    const results = await waitForResults(page)

    const count = await results.count()
    expect(count).toBeGreaterThan(0)

    // Chaque résultat est un lien avec un href non vide
    for (let i = 0; i < count; i++) {
      const href = await results.nth(i).getAttribute("href")
      expect(href).toBeTruthy()
    }
  })

  test("Cliquer sur un résultat navigue vers la page produit", async ({ page }) => {
    await typeSearchQuery(page, "lave")
    const results = await waitForResults(page)

    const firstResultHref = await results.first().getAttribute("href")
    expect(firstResultHref).toBeTruthy()

    await results.first().click()
    await page.waitForURL((url) => url.pathname !== "/", {
      timeout: TIMEOUT.DEFAULT,
    })

    // On est bien sur une page produit (URL /dechet/... ou page Wagtail)
    expect(page.url()).not.toBe("/")
  })

  test("La recherche se met à jour en temps réel", async ({ page }) => {
    // Taper une première requête
    await typeSearchQuery(page, "chaise")
    const firstResults = await waitForResults(page)
    const firstResultText = await firstResults.first().textContent()

    // Effacer et attendre que les résultats disparaissent
    const searchInput = page.locator(SEARCH_INPUT_SELECTOR)
    await searchInput.fill("")
    const results = page.locator(SEARCH_RESULTS_SELECTOR)
    await expect(results).toHaveCount(0, { timeout: TIMEOUT.DEFAULT })

    // Taper une autre requête
    await searchInput.pressSequentially("vélo", { delay: 50 })
    const newResults = await waitForResults(page)

    // Les résultats doivent être différents
    const newFirstResultText = await newResults.first().textContent()
    expect(newFirstResultText).not.toBe(firstResultText)
  })

  test("La recherche vide ne retourne pas de résultats", async ({ page }) => {
    const searchInput = page.locator(SEARCH_INPUT_SELECTOR)
    await searchInput.click()
    await searchInput.fill("")
    await searchInput.press("Enter")

    // Aucun résultat ne devrait être visible
    const results = page.locator(SEARCH_RESULTS_SELECTOR)
    await expect(results).toHaveCount(0)
  })

  test("Les résultats retournent un maximum de 10 éléments", async ({ page }) => {
    await typeSearchQuery(page, "a")
    const results = await waitForResults(page)
    const count = await results.count()
    expect(count).toBeLessThanOrEqual(10)
  })

  test("La navigation clavier fonctionne dans les résultats", async ({ page }) => {
    await typeSearchQuery(page, "lave")
    await waitForResults(page)

    // APG combobox-autocomplete-list: DOM focus stays on the textbox,
    // the active option is conveyed via aria-activedescendant on the input
    // and aria-selected on the option (no DOM focus moves to the link).
    const searchInput = page.locator(SEARCH_INPUT_SELECTOR)

    await page.keyboard.press("ArrowDown")
    await expect(searchInput).toHaveAttribute("aria-activedescendant", "option-1")
    await expect(page.locator("li#option-1")).toHaveAttribute("aria-selected", "true")

    await page.keyboard.press("ArrowDown")
    await expect(searchInput).toHaveAttribute("aria-activedescendant", "option-2")
    await expect(page.locator("li#option-2")).toHaveAttribute("aria-selected", "true")
    await expect(page.locator("li#option-1")).not.toHaveAttribute("aria-selected", /.*/)
  })

  test("Échap ferme les résultats de recherche", async ({ page }) => {
    await typeSearchQuery(page, "chaise")
    await waitForResults(page)

    await page.keyboard.press("Escape")

    // Les résultats ne devraient plus être visibles
    const results = page.locator(SEARCH_RESULTS_DROPDOWN_SELECTOR)
    expect(results).toBeHidden
  })

  test("Les résultats SearchTag portent les data attributes de tracking et non des paramètres URL", async ({
    page,
  }) => {
    await typeSearchQuery(page, "canapé d'angle")
    const results = await waitForResults(page)

    const count = await results.count()
    expect(count).toBeGreaterThan(0)

    // Trouver un résultat avec data-search-term-id (résultat de type SearchTag)
    let searchTagFound = false
    let nextUrl = ""
    for (let i = 0; i < count; i++) {
      const anchor = results.nth(i)
      const searchTermId = await anchor.getAttribute("data-search-term-id")
      if (searchTermId) {
        searchTagFound = true

        // data-search-term-id doit être un nombre
        expect(Number(searchTermId)).toBeGreaterThan(0)

        // data-search-term-name doit être présent et non vide
        const searchTermName = await anchor.getAttribute("data-search-term-name")
        expect(searchTermName).toBeTruthy()

        // Le <li> parent doit avoir l'action resultClick du next-autocomplete controller
        const li = anchor.locator("xpath=ancestor::li[1]")
        const action = await li.getAttribute("data-action")
        expect(action).toContain("click->next-autocomplete#resultClick")

        // Les paramètres ne doivent PAS être dans l'href
        const href = await anchor.getAttribute("href")
        expect(href).not.toContain("search_term_id=")
        expect(href).not.toContain("search_term=")

        nextUrl = href!
      }
    }

    expect(searchTagFound).toBe(true)
    expect(nextUrl).toBeTruthy()
    const response = await page.goto(nextUrl)
    expect(response?.status()).toBe(200)
  })
})

test.describe("Positionnement de l'autocomplete en hauteur contrainte", () => {
  // Regression: at narrow heights (iframe embedding scenario) the dropdown
  // must stay inside the document body, scrolling internally instead of
  // spilling past the bottom edge. Notion ticket 3104.
  test("La dropdown reste dans le body et scrolle en interne", async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 220 })
    await navigateTo(page, "/")

    await typeSearchQuery(page, "velo")
    await waitForResults(page)

    const measurements = await page.evaluate((selector) => {
      const frame = document.querySelector<HTMLElement>(selector)
      if (!frame) return null
      const rect = frame.getBoundingClientRect()
      return {
        bodyHeight: document.documentElement.clientHeight,
        rectTop: rect.top,
        rectBottom: rect.bottom,
        scrollHeight: frame.scrollHeight,
        clientHeight: frame.clientHeight,
        overflowY: getComputedStyle(frame).overflowY,
        hasIframeIgnore: frame.hasAttribute("data-iframe-ignore"),
      }
    }, SEARCH_RESULTS_DROPDOWN_SELECTOR)

    expect(measurements).not.toBeNull()
    // Dropdown bottom stays above body bottom (with our 8px margin).
    expect(measurements!.rectBottom).toBeLessThanOrEqual(measurements!.bodyHeight)
    // Bottom is close to body bottom — within the clamp margin, not way above.
    expect(measurements!.bodyHeight - measurements!.rectBottom).toBeLessThanOrEqual(10)
    // Content overflows the clamped frame, so the user can scroll inside.
    expect(measurements!.scrollHeight).toBeGreaterThan(measurements!.clientHeight)
    expect(measurements!.overflowY).toBe("auto")
    // iframe-resizer must skip this element when computing iframe height.
    expect(measurements!.hasIframeIgnore).toBe(true)
  })
})
