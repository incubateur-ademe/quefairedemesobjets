import { expect, test } from "@playwright/test"

test("iframe is displayed", async ({ page }) => {
    const path = require("path")
    const filePath = path.join(__dirname, "iframe_test_pages", "iframe.html")
    await page.goto(`file://${filePath}`)

    // await page.goto(
    //     "file:///Users/nicolasoudard/workspace/beta.gouv.fr/quefairedemesobjets/iframe.html",
    // ) // replace with your actual file path

    // Check if the iframe is loaded
    const iframeElement = await page.$('iframe[allow="geolocation"]')

    expect(iframeElement).not.toBeNull()
})
