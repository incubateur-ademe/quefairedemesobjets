import { test, expect } from "@playwright/test"
import { navigateTo, getIframe, TIMEOUT } from "./helpers"
import crypto from "node:crypto"
import fs from "node:fs"
import path from "node:path"

const urlsToTest = ["https://google.fr"]

test("Les pages et composants n'ont pas changé", async ({ page }) => {
  await navigateTo(page, `/lookbook`)
  const links = await page.$$("a[data-controller=lookbook-sidebar-link]")
  for (const link of links) {
    const href = await link.getAttribute("href")

    if (href) {
      urlsToTest.push(href.replace("inspect", "preview"))
    }
  }

  const errors: Error[] = []
  const sha1ToUrl: Record<string, string> = {}

  for (const pageToTest of urlsToTest) {
    await navigateTo(page, pageToTest)
    const filename = crypto.hash("sha1", pageToTest)
    sha1ToUrl[filename] = pageToTest
    const screenshotPath = `${filename}.png`
    await page.waitForTimeout(2000)
    try {
      await expect(page).toHaveScreenshot(screenshotPath, { fullPage: true })
    } catch (e) {
      errors.push(e)
    }
  }

  const mappingPath = path.join(process.cwd(), "manifest.json")
  fs.writeFileSync(mappingPath, JSON.stringify(sha1ToUrl, null, 2))
})
