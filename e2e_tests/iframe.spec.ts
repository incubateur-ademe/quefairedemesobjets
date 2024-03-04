import { expect, test } from "@playwright/test"

test("iframe is loaded with correct parameter", async ({ page }) => {
    const path = require("path")
    const filePath = path.join(__dirname, "iframe_test_pages", "iframe.html")
    await page.goto(`file://${filePath}`, { waitUntil: "networkidle" })

    const titlePage = await page.title()
    expect(titlePage).toBe("IFrame test : QFDMO")

    // Check if the iframe is loaded
    const iframeElement = await page.$("iframe")

    // test attribute allow="geolocation" is present
    const iframeAllowAttribute = await iframeElement.getAttribute("allow")
    expect(iframeAllowAttribute).toBe("geolocation")

    // <iframe  ></iframe>
    const iframeSrcAttribute = await iframeElement.getAttribute("src")
    expect(iframeSrcAttribute).toBe(
        "http://localhost:8000?iframe=1&direction=jai&first_dir=jai&action_list=reparer%7Cechanger%7Cmettreenlocation%7Crevendre",
    )

    const iframeFrameborderAttribute = await iframeElement.getAttribute("frameborder")
    expect(iframeFrameborderAttribute).toBe("0")
    const iframeScrollingAttribute = await iframeElement.getAttribute("scrolling")
    expect(iframeScrollingAttribute).toBe("no")
    const iframeAllowfullscreenAttribute =
        await iframeElement.getAttribute("allowfullscreen")
    expect(iframeAllowfullscreenAttribute).toBe("true")
    const iframeWebkitallowfullscreenAttribute = await iframeElement.getAttribute(
        "webkitallowfullscreen",
    )
    expect(iframeWebkitallowfullscreenAttribute).toBe("true")
    const iframeMozallowfullscreenAttribute =
        await iframeElement.getAttribute("mozallowfullscreen")
    expect(iframeMozallowfullscreenAttribute).toBe("true")
    const iframeStyleAttribute = await iframeElement.getAttribute("style")
    expect(iframeStyleAttribute).toContain("width: 100%;")
    expect(iframeStyleAttribute).toContain("height: 100vh;")
    expect(iframeStyleAttribute).toContain("max-width: 800px;")
})

// doesn't work on CI
// test("iframe is well resized", async ({ page }) => {
//     const path = require("path")
//     const filePath = path.join(__dirname, "iframe_test_pages", "iframe.html")
//     await page.goto(`file://${filePath}`, { waitUntil: "networkidle" })

//     // Check if the iframe is loaded
//     const iframeElement = await page.$("iframe")

//     // Get the style height and width of the iframe
//     const iframeStyleHeight = await iframeElement.evaluate((element) => {
//         return parseInt(getComputedStyle(element).height)
//     })
//     const iframeStyleWidth = await iframeElement.evaluate((element) => {
//         return parseInt(getComputedStyle(element).width)
//     })

//     // wait 5 secondes
//     await page.waitForTimeout(5000)

//     // Assert that the style height of the iframe is greater than 500
//     expect(iframeStyleHeight).toBeGreaterThan(500)
//     expect(iframeStyleWidth).toBe(800)
// })
