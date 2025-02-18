import { expect, test } from "@playwright/test";
import { hideDjangoToolbar, searchDummyAdresse } from "./helpers";

test("Desktop | La carte affiche la légende après une recherche", async ({ page }) => {
    // Navigate to the carte page
    await page.goto(`http://localhost:8000/carte`, { waitUntil: "networkidle" });
    await hideDjangoToolbar(page)

    await expect(page.getByTestId("carte-legend")).toBeHidden()

    // Fill "Adresse" autocomplete input
    await searchDummyAdresse(page)
    await expect(page.getByTestId("carte-legend")).toBeVisible()
})
