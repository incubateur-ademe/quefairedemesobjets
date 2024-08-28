import { expect, test } from "@playwright/test"

test("Filtres avancés s'ouvrent et se ferment", async ({ page }) => {
    await page.goto(`http://localhost:8000/`, {
        waitUntil: "networkidle",
    })
    await page.locator("#djHideToolBarButton").click()
    await page.locator("button[data-testid=advanced-filters]").click()
    await expect(page.locator("[data-testid=advanced-filters-modal] .fr-modal__content h4")).toBeInViewport()
    await page.locator("[data-testid=advanced-filters-modal] .fr-modal__header button").click()
    await expect(page.locator("[data-testid=advanced-filters-modal] .fr-modal__content h4")).toBeHidden()
})
