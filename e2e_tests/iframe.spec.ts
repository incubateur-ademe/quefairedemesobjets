import { expect } from "@playwright/test"
import { test } from "./config"
import { hideDjangoToolbar } from "./helpers"

test("Desktop | iframe formulaire is loaded with correct parameters", async ({
  page,
  carteUrl,
}) => {
  await page.goto(`/test_iframe`, { waitUntil: "domcontentloaded" })

  const titlePage = await page.title()
  expect(titlePage).toBe("IFrame test : QFDMO")

  const iframeElement = await page.$("iframe")
  const attributes = await Promise.all([
    iframeElement?.getAttribute("allow"),
    iframeElement?.getAttribute("src"),
    iframeElement?.getAttribute("frameborder"),
    iframeElement?.getAttribute("scrolling"),
    iframeElement?.getAttribute("allowfullscreen"),
    iframeElement?.getAttribute("style"),
    iframeElement?.getAttribute("title"),
  ])

  const [allow, src, frameborder, scrolling, allowfullscreen, style, title] = attributes

  expect(allow).toBe("geolocation; clipboard-write")
  expect(src).toBe(
    `${carteUrl}/formulaire?direction=jai&first_dir=jai&action_list=reparer%7Cechanger%7Cmettreenlocation%7Crevendre`,
  )
  expect(frameborder).toBe("0")
  expect(scrolling).toBe("no")
  expect(allowfullscreen).toBe("true")
  expect(style).toContain("width: 100%;")
  expect(style).toContain("height: 720px;")
  expect(style).toContain("max-width: 100%;")
  expect(title).toBe("Longue vie aux objets")
})

test("Desktop | legacy iframe urls still work", async ({ page }) => {
  await page.goto(
    `/formulaire?direction=jai&first_dir=jai&action_list=reparer%7Cechanger%7Cmettreenlocation%7Crevendre`,
    { waitUntil: "domcontentloaded" },
  )
  await expect(page).toHaveURL(
    `/formulaire?direction=jai&first_dir=jai&action_list=reparer%7Cechanger%7Cmettreenlocation%7Crevendre`,
  )
  await page.goto(
    `/carte?action_list=reparer%7Cdonner%7Cechanger%7Cpreter%7Cemprunter%7Clouer%7Cmettreenlocation%7Cacheter%7Crevendre&epci_codes=200055887&limit=50`,
    { waitUntil: "domcontentloaded" },
  )
  await expect(page).toHaveURL(
    `/carte?action_list=reparer%7Cdonner%7Cechanger%7Cpreter%7Cemprunter%7Clouer%7Cmettreenlocation%7Cacheter%7Crevendre&epci_codes=200055887&limit=50`,
  )
})

// test("Desktop | form is visible in the iframe", async ({ page }) => {
//   await page.goto(`/test_iframe`, { waitUntil: "domcontentloaded" })

//   const iframeElement = page.locator("iframe")
//   const iframe = iframeElement?.contentFrame()
//   const form = iframe?.locator("#search_form")
//   expect(form).not.toBeNull()

//   const formHeight = await iframe?.$eval(
//     "[data-testid='form-content']",
//     (el) => el.offsetHeight,
//   )
//   expect(formHeight).toBeGreaterThan(600)
// })
test("Desktop | form is visible in the iframe", async ({ page }) => {
  await page.goto(`/test_iframe`, { waitUntil: "domcontentloaded" })

  const iframeElement = page.frameLocator("iframe[title='Longue vie aux objets']")

  // Check if the form exists
  const form = iframeElement.locator("#search_form")
  await expect(form).toBeVisible()

  // Check form height
  const formHeight = await iframeElement
    .locator("[data-testid='form-content']")
    .evaluate((el) => el.offsetHeight)
  expect(formHeight).toBeGreaterThan(600)
})

test("Desktop | iframe with 0px parent height displays correctly", async ({ page }) => {
  await page.goto(`/test_iframe?carte_with_defaults=1`, {
    waitUntil: "domcontentloaded",
  })
  await expect(page).toHaveScreenshot("iframe.png")

  await page.goto(`/test_iframe?noheight=1&carte=1`, { waitUntil: "domcontentloaded" })
  await page.evaluate(() => {
    document
      .querySelector("[data-testid=iframe-no-height-wrapper]")
      ?.setAttribute("style", "")
  })
  await page.waitForTimeout(1000)
  await expect(page).toHaveScreenshot("iframe.png")
})

test("Desktop | iframe cannot read the referrer when referrerPolicy is set to no-referrer", async ({
  page,
}) => {
  await page.goto(`/test_iframe?carte=1&noreferrer`, { waitUntil: "domcontentloaded" })

  // Get the content frame of the iframe
  const iframeElement = await page.$("iframe[referrerpolicy='no-referrer']")
  const iframe = await iframeElement?.contentFrame()
  expect(iframe).toBeTruthy()

  // Evaluate the referrer inside the iframe
  const referrer = await iframe?.evaluate(() => document.referrer)

  // Assert that the referrer is set and not undefined
  expect(referrer).toBe("")
})

test("Desktop | iframe can read the referrer when referrerPolicy is not set", async ({
  page,
  assistantUrl,
}) => {
  await page.goto(`${assistantUrl}/test_iframe?carte=1`, {
    waitUntil: "domcontentloaded",
  })

  // Get the content frame of the iframe
  const iframeElement = await page.$("iframe[data-testid='assistant']")
  const iframe = await iframeElement?.contentFrame()
  expect(iframe).not.toBeNull()
  hideDjangoToolbar(iframe)

  // Evaluate the referrer inside the iframe
  const referrer = await iframe!.evaluate(() => document.referrer)

  // Assert that the referrer is set and not undefined
  expect(referrer).toBe(`${assistantUrl}/test_iframe?carte=1`)
})

test("Desktop | iFrame mode persists across navigation", async ({
  page,
  assistantUrl,
}) => {
  test.slow()
  // Starting URL - change this to your site's starting point
  await page.goto(`/lookbook/inspect/iframe/assistant/`, { waitUntil: "networkidle" })
  const iframeElement = page.locator(
    "iframe[title='Écran | Que Faire de mes objets & déchets']",
  )
  const iframe = iframeElement?.contentFrame()
  expect(iframe).not.toBeNull()

  for (let i = 0; i < 50; i++) {
    // Check that header.fr-header is NOT present
    await expect(iframe.locator("body")).toHaveAttribute(
      "data-state-iframe-value",
      "true",
    )

    // Find all internal links on the page (href starting with the same origin)
    const links = iframe.locator(`a[href^="${assistantUrl}"]`)

    // Pick a random internal link to click
    const count = await links.count()
    const randomLink = links.nth(Math.floor(Math.random() * count))
    if (await randomLink.isVisible()) {
      await randomLink.click()
    }
  }
})
