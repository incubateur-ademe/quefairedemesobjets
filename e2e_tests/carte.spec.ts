import { expect, test } from "@playwright/test";
import { hideDjangoToolbar, searchDummyAdresse } from "./helpers";

test("Recherche et modification d'une recherche", async ({ page }) => {
    // Navigate to the carte page
    await page.goto(`http://localhost:8000/carte`, { waitUntil: "networkidle" });
    await hideDjangoToolbar(page)

    expect(page.getByTestId("carte-legend")).toBeHidden()

    // Fill "Adresse" autocomplete input
    await searchDummyAdresse(page)
    await expect(page.getByTestId("carte-legend")).toBeVisible()
})
