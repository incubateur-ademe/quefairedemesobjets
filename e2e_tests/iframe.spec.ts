import { expect, test } from "@playwright/test"

test("iframe style height", async ({ page }) => {
    const path = require("path")
    const filePath = path.join(__dirname, "iframe_test_pages", "iframe.html")
    await page.goto(`file://${filePath}`)

    // Check if the iframe is loaded
    const iframeElement = await page.$('iframe[allow="geolocation"]')

    // Get the style height and width of the iframe
    const iframeStyleHeight = await iframeElement.evaluate((element) => {
        return parseInt(getComputedStyle(element).height)
    })
    const iframeStyleWidth = await iframeElement.evaluate((element) => {
        return parseInt(getComputedStyle(element).width)
    })

    // Assert that the style height of the iframe is greater than 500
    expect(iframeStyleHeight).toBeGreaterThan(500)
    expect(iframeStyleWidth).toBe(800)
})
