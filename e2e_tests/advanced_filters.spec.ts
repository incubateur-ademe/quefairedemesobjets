import { expect, test } from "@playwright/test"

async function testAdvancedFilters(page) {
  await page.locator("#djHideToolBarButton").click()
  await page.locator("button[data-testid=advanced-filters]").click()
  await expect(page.locator("[data-testid=advanced-filters-modal] .fr-modal__content h4")).toBeInViewport()
  await page.locator("[data-testid=advanced-filters-modal] .fr-modal__header button").click()
  await expect(page.locator("[data-testid=advanced-filters-modal] .fr-modal__content h4")).toBeHidden()
}

test("Filtres avancés s'ouvrent et se ferment en mode iframe", async ({ page }) => {
    await page.goto(`http://localhost:8000/?iframe`, {
        waitUntil: "networkidle",
    })
    await testAdvancedFilters(page)
})

test("Filtres avancés s'ouvrent et se ferment en mode carte", async ({ page }) => {
    await page.goto(`http://localhost:8000/?carte`, {
        waitUntil: "networkidle",
    })
    await testAdvancedFilters(page)
})

test("Filtres avancés s'ouvrent et se ferment en mode formulaire", async ({ page }) => {
    await page.goto(`http://localhost:8000/?carte`, {
        waitUntil: "networkidle",
    })
    await testAdvancedFilters(page)
})
