import { test as base, expect } from "@playwright/test"

export const test = base.extend<{ forEachTest: void }>({
  forEachTest: [
    async ({ page }, use, testInfo) => {
      await use()
      const hasRegressionTag = testInfo.tags.includes("@regression")
      if (hasRegressionTag) {
        const filename = crypto.hash("sha1", `${testInfo.titlePath}-${page.url()}`)
        await expect.soft(page).toHaveScreenshot({
          fullPage: true,
        })
      }
    },
    { auto: true },
  ],
})
