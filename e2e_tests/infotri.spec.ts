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
    expect(scriptUrl).toContain("/infotri/")

    // The configurateur script creates an iframe
    const iframe = page.frameLocator("iframe").first()
    await expect(iframe.locator("body")).toBeAttached({ timeout: 10000 })

    // Step 1: Select a category (radio button)
    await iframe.locator('input[name="categorie"][value="textile"]').click()

    // Wait for the form to reload with the consigne section visible
    await expect(iframe.locator('input[name="consigne"]').first()).toBeVisible({
      timeout: 10000,
    })

    // Step 2: Select a consigne (radio button)
    await iframe.locator('input[name="consigne"][value="1"]').click()

    // Wait for the checkbox to appear
    await expect(iframe.locator('input[name="avec_phrase"]')).toBeVisible({
      timeout: 10000,
    })

    // Step 3: Toggle the "Afficher la phrase" checkbox
    await iframe.locator('input[name="avec_phrase"]').check()

    // Step 4: Click the "Générer le code" button
    await expect(iframe.locator('button[name="show_code"][value="true"]')).toBeVisible({
      timeout: 10000,
    })
    await iframe.locator('button[name="show_code"][value="true"]').click()

    // Step 5: Verify the generated script tag is visible
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
    expect(scriptSrc).toBe(scriptUrl?.trim())

    // Step 8: Verify the script URL returns a 200 status code
    const response = await page.request.get(scriptSrc)
    expect(response.status()).toBe(200)
  })
})
