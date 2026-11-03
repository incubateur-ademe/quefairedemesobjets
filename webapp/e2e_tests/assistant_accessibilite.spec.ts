import { AxeBuilder } from "@axe-core/playwright"
import { expect, test, type Page } from "@playwright/test"
import { dragAssistantMap, mockAssistantAddressServices, navigateTo } from "./helpers"

// Out at sea: no place within reach, in the sample database as in production.
const AU_LARGE = "longitude=-5.5&latitude=46"

async function expectNoViolations(page: Page) {
  // Turbo marks the document busy while a visit renders.
  await expect(page.locator("html")).not.toHaveAttribute("aria-busy")
  const results = await new AxeBuilder({ page })
    // The canvas is decorative: the accessible list carries the information.
    .exclude(".maplibregl-canvas")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze()
  expect(results.violations).toEqual([])
}

test.describe("♿ Accessibilité de l'assistant", () => {
  test("Les écrans sont accessibles et la recherche se fait au clavier", async ({
    page,
  }) => {
    await mockAssistantAddressServices(page)

    await test.step("Accueil, au clavier", async () => {
      await navigateTo(page, "/assistant/")
      await expectNoViolations(page)

      await page.keyboard.press("Tab")
      await expect(page.locator(".qfa-skiplink")).toBeFocused()

      const objet = page.locator("#recherche-objet-champ")
      await objet.fill("vél")
      await expect(objet).toHaveAttribute("aria-expanded", "true")
      await objet.press("Escape")
      await expect(objet).toHaveAttribute("aria-expanded", "false")

      await objet.pressSequentially("o")
      await expect(objet).toHaveAttribute("aria-expanded", "true")
      await objet.press("ArrowDown")
      await expect(objet).toHaveAttribute("aria-activedescendant", /option-0$/)
      await objet.press("Enter")
      await expect(objet).toHaveValue("Vélo")

      const adresse = page.locator("#recherche-adresse-champ")
      await adresse.fill("Montb")
      await expect(adresse).toHaveAttribute("aria-expanded", "true")
      await adresse.press("ArrowDown")
      await adresse.press("Enter")
      await expect(adresse).toHaveValue("Montbéliard")

      await page.keyboard.press("Tab")
      await page.keyboard.press("Enter")
      await expect(page).toHaveURL(/\/assistant\/objet\/velo\//)
    })

    await test.step("Fiche", async () => {
      await expectNoViolations(page)
    })

    await test.step("Solutions sans aucun lieu", async () => {
      await navigateTo(
        page,
        `/assistant/solutions/?geste=reparer&fiche=velo&adresse=Au%20large&${AU_LARGE}`,
      )
      await expect(page.locator(".qfa-carte__message")).toContainText(
        "Aucun lieu trouvé ici",
      )
      await expectNoViolations(page)

      const explored = page.waitForResponse((r) => r.url().includes("bbox="))
      await dragAssistantMap(page, 40, 40)
      await explored
    })
  })
})
