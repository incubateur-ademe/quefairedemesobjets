import { expect, test } from "@playwright/test"
import { hideDjangoToolbar } from "./helpers"

async function searchInCarteMode(page){
  await page.locator("input#id_adresse").click()
  await page.locator("input#id_adresse").fill("Paris")
  await page.locator("#id_adresseautocomplete-list.autocomplete-items div:nth-of-type(2)").click()
}

async function openAdvancedFilters(page, dataTestId="advanced-filters") {
  // Explicitely wait for addresses to load
  await page.waitForTimeout(5000);
  await page.locator(`button[data-testid=${dataTestId}]`).click()
  await expect(page.locator("[data-testid=advanced-filters-modal] .fr-modal__content h2")).toBeInViewport()
  await page.locator("[data-testid=advanced-filters-modal] .fr-modal__header button").click()
  await expect(page.locator("[data-testid=advanced-filters-modal] .fr-modal__content h2")).toBeHidden()
}

test("Filtres avancés s'ouvrent et se ferment en mode formulaire", async ({ page }) => {
    await page.goto(`http://localhost:8000/formulaire`, {
        waitUntil: "networkidle",
    })
    await hideDjangoToolbar(page)
    await openAdvancedFilters(page)
})

test("Desktop | Filtres avancés s'ouvrent et se ferment en mode carte", async ({ page }) => {
    await page.goto(`http://localhost:8000/carte`, {
        waitUntil: "networkidle",
    })
    await hideDjangoToolbar(page)
    await searchInCarteMode(page)
    await openAdvancedFilters(page, "advanced-filters-in-legend")
})

test("Mobile | Filtres avancés s'ouvrent et se ferment en mode carte", async ({ page }) => {
    await page.goto(`http://localhost:8000/carte`, {
        waitUntil: "networkidle",
    })
    await hideDjangoToolbar(page)
    await searchInCarteMode(page)
    await openAdvancedFilters(page)
})
