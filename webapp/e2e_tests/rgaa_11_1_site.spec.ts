import { test, expect } from "@playwright/test"
import { navigateTo } from "./helpers"

const SEARCH_LABEL = "Rechercher un objet ou un déchet"
const HOME_SEARCH_LABEL = "Entrez un objet ou un déchet"

test.describe("♿ RGAA 11.1 — Étiquette du champ de recherche de l'en-tête", () => {
  test("Les champs de recherche de l'en-tête et de l'accueil ont un label et un title identiques", async ({
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

    const homeInput = page.locator("#id_home-search")
    const homeLabel = page.locator('label[for="id_home-search"]')
    await expect(homeLabel).toHaveText(HOME_SEARCH_LABEL)
    await expect(homeInput).toHaveAttribute("title", HOME_SEARCH_LABEL)
  })
})
