import { expect, test } from "@playwright/test"

test.describe("🌐 Compatibilité Navigateur", () => {
  test("Browser version alert is not displayed", async ({ page }) => {
    await page.goto(`/formulaire`, { waitUntil: "domcontentloaded" })

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
