import { test as base, expect } from "@playwright/test"
import crypto from "node:crypto"

export const test = base.extend<{ forEachTest: void }>({
  forEachTest: [
    async ({ page }, use, testInfo) => {
      await use()
      const hasRegressionTag = testInfo.tags.includes("@regression")
      if (hasRegressionTag) {
        const filename = crypto.hash("sha1", page.url())
        await expect.soft(page).toHaveScreenshot(filename, { fullPage: true })
      }
    },
    { auto: true },
  ],
})
