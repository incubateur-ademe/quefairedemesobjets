import { test, expect } from "@playwright/test"
import { navigateTo, getIframe, TIMEOUT } from "./helpers"
import crypto from "node:crypto"
import fs from "node:fs"
import path from "node:path"

interface PageResult {
  url: string
  status?: number
  errors: string[]
}

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

  const manifest: Record<string, PageResult> = {}
  let hasErrors = false

  for (const pageToTest of urlsToTest) {
    const filename = crypto.hash("sha1", pageToTest)
    const result: PageResult = { url: pageToTest, errors: [] }

    try {
      const response = await page.goto(pageToTest, { waitUntil: "domcontentloaded" })
      result.status = response?.status()

      if (result.status !== 200) {
        result.errors.push(`HTTP ${result.status}`)
        hasErrors = true
        manifest[filename] = result
        continue
      }

      await page.waitForTimeout(2000)

      try {
        await expect(page).toHaveScreenshot(`${filename}.png`, { fullPage: true })
      } catch (e) {
        result.errors.push("screenshot_mismatch")
        hasErrors = true
      }
    } catch (e) {
      result.errors.push(`navigation_error: ${(e as Error).message}`)
      hasErrors = true
    }

    manifest[filename] = result
  }

  const mappingPath = path.join(process.cwd(), "__regression_manifest.json")
  fs.writeFileSync(mappingPath, JSON.stringify(manifest, null, 2))

  expect(
    hasErrors,
    `Regression errors detected:\n${Object.values(manifest)
      .filter((r) => r.errors.length > 0)
      .map((r) => `  ${r.url}: ${r.errors.join(", ")}`)
      .join("\n")}`,
  ).toBe(false)
})
