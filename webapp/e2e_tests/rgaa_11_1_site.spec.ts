import { test, expect } from "@playwright/test"
import { navigateTo } from "./helpers"

const SEARCH_LABEL = "Rechercher un objet ou un déchet"

test.describe("♿ RGAA 11.1 — Étiquette du champ de recherche de l'en-tête", () => {
  test("Le champ de recherche de l'en-tête a un label et un title identiques", async ({
    page,
  }) => {
    await navigateTo(page, "/")

    const input = page.locator("#id_header-autocomplete-search")
    await expect(input).toBeAttached()
    await expect(input).toHaveAttribute("title", SEARCH_LABEL)

    const label = page.locator('label[for="id_header-autocomplete-search"]')
    await expect(label).toHaveText(SEARCH_LABEL)

    await expect(
      page.locator("#search-bar").getByRole("combobox", { name: SEARCH_LABEL }),
    ).toBeAttached()
  })
})
