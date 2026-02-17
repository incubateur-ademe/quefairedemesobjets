import { test, expect } from "@playwright/test"

test.describe("🏷️ Configurateur Info-tri", () => {
  test("Le configurateur génère un script tag avec une URL valide", async ({
    page,
  }) => {
    await page.goto("/lookbook/preview/tests/t_16_infotri_configurator", {
      waitUntil: "domcontentloaded",
    })

    // Verify the infotri_script_url template tag renders a valid URL
    const scriptUrlElement = page.locator('[data-testid="infotri-script-url"]')
    const scriptUrl = await scriptUrlElement.textContent()
    expect(scriptUrl).toBeTruthy()
    expect(scriptUrl!.trim()).toContain("/infotri/")

    // The configurateur script creates a same-origin iframe
    const iframe = page.frameLocator("iframe").first()
    await expect(iframe.locator("body")).toBeAttached({ timeout: 10000 })

    // Step 1: Select a category
    await iframe.getByText("Textiles d'habillement", { exact: true }).click()

    // Wait for the consigne section to appear after form auto-submit
    await expect(
      iframe.getByText("À déposer dans un conteneur", { exact: true }),
    ).toBeVisible({ timeout: 10000 })

    // Step 2: Select a consigne
    await iframe.getByText("À déposer dans un conteneur", { exact: true }).click()

    // Wait for the checkbox to appear
    await expect(iframe.getByText("Afficher la phrase")).toBeVisible({
      timeout: 10000,
    })

    // Step 3: Check the "Afficher la phrase" checkbox
    await iframe.getByText("Afficher la phrase").click()

    // Step 4: Click the "Générer le code" button
    await expect(iframe.getByRole("button", { name: "Générer le code" })).toBeVisible({
      timeout: 10000,
    })
    await iframe.getByRole("button", { name: "Générer le code" }).click()

    // Step 5: Verify the generated code block is visible
    const codeBlock = iframe.locator('[data-copy-target="toCopy"]')
    await expect(codeBlock).toBeVisible({ timeout: 10000 })

    // Step 6: Verify the script tag content contains expected parts
    const codeContent = await codeBlock.textContent()
    expect(codeContent).toContain("<script")
    expect(codeContent).toContain("categorie=textile")
    expect(codeContent).toContain("consigne=1")
    expect(codeContent).toContain("avec_phrase=true")

    // Step 7: Verify the generated src matches the template tag URL
    const srcMatch = codeContent?.match(/src="([^"]+)"/)
    expect(srcMatch).toBeTruthy()
    const scriptSrc = srcMatch![1]
    expect(scriptSrc).toBe(scriptUrl!.trim())

    // Step 8: Verify the script URL returns a 200 with correct content type
    const response = await page.request.get(scriptSrc, {
      ignoreHTTPSErrors: true,
    })
    expect(response.status()).toBe(200)
    expect(response.headers()["content-type"]).toContain("text/javascript")
  })

  const categories = [
    { label: "Tous", value: "tous" },
    { label: "Textiles d'habillement", value: "textile" },
    { label: "Linges de maison", value: "vetement" },
    { label: "Chaussures", value: "chaussures" },
  ]

  for (const { label, value } of categories) {
    test(`La catégorie "${label}" affiche un pictogramme SVG à côté du Cartouche France`, async ({
      page,
    }) => {
      await page.goto(`/infotri/?categorie=${value}`, {
        waitUntil: "domcontentloaded",
      })

      // Wait for the Cartouche France to be visible
      await expect(page.getByRole("img", { name: "Cartouche France" })).toBeVisible({
        timeout: 10000,
      })

      // Verify a pictogramme SVG is the next sibling of Cartouche France
      const hasPictogramme = await page.evaluate(() => {
        const cartouche = document.querySelector('[aria-label="Cartouche France"]')
        const next = cartouche?.nextElementSibling
        return (
          next?.tagName === "svg" &&
          next?.getAttribute("aria-label")?.startsWith("Pictogramme")
        )
      })
      expect(hasPictogramme).toBe(true)
    })
  }
})
