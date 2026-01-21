import { expect, test } from "@playwright/test"
import { navigateTo } from "./helpers"

test.describe("🌐 Compatibilité Navigateur", () => {
  test("L'alerte de version de navigateur obsolète n'est pas affichée pour les navigateurs modernes", async ({
    page,
  }) => {
    await navigateTo(page, `/formulaire`)

    const titlePage = await page.title()
    expect(titlePage).toBe("Longue vie aux objets")

    // Check that the browser version alert is not displayed
    const alert = await page.$("#obsolete_browser_message")
    expect(await alert?.getAttribute("class")).toContain("qf-hidden")

    // check libelé "L'application nécessite Javascript pour être exécutée correctement" is inside a noscript tag
    const noscript = await page.$("noscript")
    const noscriptContent = await noscript?.textContent()
    expect(noscriptContent).toContain(
      "L'application nécessite Javascript pour être exécutée correctement",
    )
  })
})
