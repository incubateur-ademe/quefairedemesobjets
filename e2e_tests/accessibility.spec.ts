import { AxeBuilder } from "@axe-core/playwright"
import { expect, test } from "@playwright/test"

// test("formulaire iFrame is WCAG compliant", async ({ page }) => {
//   await page.goto(`http://localhost:8000/test_iframe`, { waitUntil: "networkidle" })

//   const accessibilityScanResults = await new AxeBuilder({ page })
//     .include("iframe") // restriction du scan à l'iframe uniquement
//     .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])  // TODO : trouver quelle règle se rapproche le plus du RGAA
//     .analyze()

//   expect(accessibilityScanResults.violations).toEqual([])
// })

// test("carte iFrame is WCAG compliant", async ({ page }) => {
//   await page.goto(`http://localhost:8000/test_iframe?carte`, { waitUntil: "networkidle" })

//   const accessibilityScanResults = await new AxeBuilder({ page })
//     .include("iframe") // restriction du scan à l'iframe uniquement
//     .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])  // TODO : trouver quelle règle se rapproche le plus du RGAA
//     .analyze()

//   expect(accessibilityScanResults.violations).toEqual([])
// })
