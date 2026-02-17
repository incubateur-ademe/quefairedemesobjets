import { test as base } from "@playwright/test"
import crypto from "node:crypto"

export const test = base.extend<{ forEachTest: void }>({
  forEachTest: [
    async ({ page }, use, testInfo) => {
      await use()
      const hasRegressionTag = testInfo.tags.includes("@regression")
      if (hasRegressionTag) {
        const filename = crypto.hash("sha1", page.url())
        await expect(page).toHaveScreenshot(filename, { fullPage: true })
      }
      // This code runs after every test.
      console.log("Last URL:", page.url())
    },
    { auto: true },
  ], // automatically starts for every test.
})
