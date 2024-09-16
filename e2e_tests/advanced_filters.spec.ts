import { expect, test } from "@playwright/test"

async function hideDjangoToolbar(page) {
  await page.locator("#djHideToolBarButton").click()
}

async function searchInCarteMode(page){
  await page.locator("input#adresse").click()
  await page.locator("input#adresse").fill("10 rue de la paix")
  await page.locator("#adresseautocomplete-list.autocomplete-items div:nth-of-type(2)").click()
  await page.locator("button[data-testid=rechercher-adresses-submit]").click()
}

async function openAdvancedFilters(page, dataTestId="advanced-filters") {
  await page.waitForTimeout(3000);
  await page.locator(`button[data-testid=${dataTestId}]`).click()
  await expect(page.locator("[data-testid=advanced-filters-modal] .fr-modal__content h4")).toBeInViewport()
  await page.locator("[data-testid=advanced-filters-modal] .fr-modal__header button").click()
  await expect(page.locator("[data-testid=advanced-filters-modal] .fr-modal__content h4")).toBeHidden()
}

test("Filtres avancés s'ouvrent et se ferment en mode iframe", async ({ page }) => {
    await page.goto(`http://localhost:8000/?iframe`, {
        waitUntil: "networkidle",
    })
    await hideDjangoToolbar(page)
    await openAdvancedFilters(page)
})

test("Filtres avancés s'ouvrent et se ferment en mode carte", async ({ page }) => {
    await page.goto(`http://localhost:8000/?carte`, {
        waitUntil: "networkidle",
    })
    await hideDjangoToolbar(page)
    await searchInCarteMode(page)
    await openAdvancedFilters(page, "advanced-filters-in-legend")
})

test("Filtres avancés s'ouvrent et se ferment en mode formulaire", async ({ page }) => {
    await page.goto(`http://localhost:8000/`, {
        waitUntil: "networkidle",
    })
    await hideDjangoToolbar(page)
    await openAdvancedFilters(page)
})
