import { expect, test } from "@playwright/test"
import exp = require("constants")

test("iframe is loaded with correct parameter", async ({ page }) => {
  await page.goto(`http://localhost:8000/test_iframe`, { waitUntil: "networkidle" })

  const titlePage = await page.title()
  expect(titlePage).toBe("IFrame test : QFDMO")

  // Check if the iframe is loaded
  const iframeElement = await page.$("iframe")

  // test attribute allow="geolocation" is present
  const iframeAllowAttribute = await iframeElement?.getAttribute("allow")
  expect(iframeAllowAttribute).toBe("geolocation; clipboard-write")

  // <iframe  ></iframe>
  const iframeSrcAttribute = await iframeElement?.getAttribute("src")
  expect(iframeSrcAttribute).toBe(
    "http://localhost:8000?iframe=1&direction=jai&first_dir=jai&action_list=reparer%7Cechanger%7Cmettreenlocation%7Crevendre",
  )

  const iframeFrameborderAttribute = await iframeElement?.getAttribute("frameborder")
  expect(iframeFrameborderAttribute).toBe("0")
  const iframeScrollingAttribute = await iframeElement?.getAttribute("scrolling")
  expect(iframeScrollingAttribute).toBe("no")
  const iframeAllowfullscreenAttribute =
    await iframeElement?.getAttribute("allowfullscreen")
  expect(iframeAllowfullscreenAttribute).toBe("true")
  const iframeStyleAttribute = await iframeElement?.getAttribute("style")
  expect(iframeStyleAttribute).toContain("width: 100%;")
  expect(iframeStyleAttribute).toContain("height: 100vh;")
  expect(iframeStyleAttribute).toContain("max-width: 800px;")
  const iframeTitleAttribute = await iframeElement?.getAttribute("title")
  expect(iframeTitleAttribute).toBe("Longue vie aux objets")
})

test("the form is visible in the iframe", async ({ page }) => {
  await page.goto(`http://localhost:8000/test_iframe`, { waitUntil: "networkidle" })

  const iframeElement = await page.$("iframe")
  const iframe = await iframeElement?.contentFrame()
  const form = await iframe?.$("#search_form")
  expect(form).not.toBeNull()

  const height = await iframe?.$eval(
    "[data-test-id='form-content']",
    (el) => (el as HTMLElement).offsetHeight,
  )
  expect(height).toBeGreaterThan(600)
})

// test("rechercher dans cette zone", async ({ page }) => {
//   await page.goto(`http://localhost:8000/test_iframe?carte=1`, {
//     waitUntil: "networkidle",
//   })
//   await page.frameLocator("#lvao_iframe").locator("#djHideToolBarButton").click()
//   expect(page.frameLocator("#lvao_iframe").getByTestId("searchInZone")).toBeHidden()
//   await page.locator("#lvao_iframe").hover()
//   await page.mouse.down()
//   await page.mouse.move(2000, 2000)
//   await page.mouse.up()
//   await page.waitForTimeout(2000) // ensures iframe has enough time to load properly
//   expect(page.frameLocator("#lvao_iframe").getByTestId("searchInZone")).toBeVisible()
// })

test("iframe loaded with 0px parent height looks good", async ({ page }) => {
  await page.goto(`http://localhost:8000/test_iframe?carte=1`, {
    waitUntil: "networkidle",
  })
  await expect(page).toHaveScreenshot(`iframe.png`)
  await page.goto(`http://localhost:8000/test_iframe?no-height=1&carte=1`, {
    waitUntil: "networkidle",
  })
  await page.evaluate(() =>
    document
      .querySelector("[data-testid=iframe-no-height-wrapper]")
      ?.setAttribute("style", ""),
  )
  await page.waitForTimeout(1000) // ensures iframe has enough time to load properly
  await expect(page).toHaveScreenshot(`iframe.png`)
})
