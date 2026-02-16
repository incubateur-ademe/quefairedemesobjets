import { test, expect } from "@playwright/test"
import { navigateTo, getIframe, TIMEOUT } from "./helpers"
import crypto from "node:crypto"

const urlsToTest = ["https://google.fr"]

test("Les pages et composants n'ont pas changé", async ({ page }) => {
  await navigateTo(page, `/lookbook`)
  const links = await page.$$("a[data-controller=lookbook-sidebar-link]")
  // todo: remove before merge
  let count = 0
  for (const link of links) {
    const href = await link.getAttribute("href")

    if (href && count < 3) {
      urlsToTest.push(href.replace("inspect", "preview"))
    }
    count += 1
  }

  for (const pageToTest of urlsToTest) {
    await navigateTo(page, pageToTest)
    const filename = crypto.hash("sha1", pageToTest)
    const screenshotPath = `${filename}.png`
    await page.waitForTimeout(2000)
    await expect(page).toHaveScreenshot(screenshotPath)
  }
})
