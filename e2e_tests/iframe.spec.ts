import { expect, test } from "@playwright/test"
import exp = require("constants")

test("iframe is loaded with correct parameter", async ({ page }) => {
    await page.goto(`http://localhost:8000/test_iframe`, { waitUntil: "networkidle" })

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

test("the form is visible in the iframe", async ({ page }) => {
    await page.goto(`http://localhost:8000/test_iframe`, { waitUntil: "networkidle" })

    const iframeElement = await page.$("iframe")
    const iframe = await iframeElement.contentFrame()
    const form = await iframe.$("#search_form")
    expect(form).not.toBeNull()

    const height = await iframe.$eval(
        "[data-test-id='form-content']",
        (el) => (el as HTMLElement).offsetHeight,
    )
    expect(height).toBeGreaterThan(600)
})
