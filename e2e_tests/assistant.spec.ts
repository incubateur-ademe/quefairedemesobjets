import { expect, test } from "@playwright/test";
import { hideDjangoToolbar, searchDummyAdresse } from "./helpers";

test.describe("Tests de l'assistant", () => {

  test("Desktop | La carte s'affiche sur une fiche déchet/objet", async ({ page }) => {
    // Navigate to the carte page
    await page.goto(`/dechet/lave-linge`, { waitUntil: "networkidle" });
    await hideDjangoToolbar(page)
    await searchDummyAdresse(page)
    await expect(page.getByTestId("carte-legend")).toBeVisible()
  })
})
