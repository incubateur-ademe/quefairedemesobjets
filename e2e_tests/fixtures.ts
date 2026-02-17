import { test as base, expect } from "@playwright/test"

export const test = base.extend<{ forEachTest: void }>({
  forEachTest: [
    async ({ page }, use, testInfo) => {
      await use()
      const hasRegressionTag = testInfo.tags.includes("@regression")
      if (hasRegressionTag) {
        await expect
          .soft(page)
          .toHaveScreenshot(`${testInfo.titlePath}-${page.url()}.png`, {
            fullPage: true,
          })
      }
    },
    { auto: true },
  ],
})
