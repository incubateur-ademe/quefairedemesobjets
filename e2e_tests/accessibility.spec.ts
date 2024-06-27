import { AxeBuilder } from "@axe-core/playwright"

import { expect, test } from "@playwright/test"

test("iFrame is WCAG compliant", async ({ page }) => {
  await page.goto(`http://localhost:8000/test_iframe`, { waitUntil: "networkidle" })

  const accessibilityScanResults = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze()
  expect(accessibilityScanResults.violations).toEqual([])

  await browser.close();

})
