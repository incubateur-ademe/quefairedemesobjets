import { test } from "./fixtures"
import { navigateTo } from "./helpers"

async function loginAsAdmin(page) {
  await navigateTo(page, "/admin/login/")
  await page.locator('input[name="username"]').fill("admin")
  await page.locator('input[name="password"]').fill("admin")
  await page.locator('[type="submit"]').click()
  await page.waitForURL("**/admin/")
}

test("debug search", async ({ page }) => {
  page.on("console", (msg) => console.log(`PAGE [${msg.type()}]:`, msg.text()))
  await loginAsAdmin(page)
  await navigateTo(page, "/admin/qfdmo/revisionacteur/")
  await page.locator("#result_list .field-nom a").first().click()
  await page.waitForLoadState("domcontentloaded")

  const info = await page.evaluate(() => {
    const s = (window as any).stimulus
    const identifiers = [...(s?.router?.modulesByIdentifier?.keys() || [])]
    const actionAttr = document.querySelector('[data-controller="map-search"]')?.dataset
      ?.controller
    const buttonActionAttr = document
      .querySelector("[data-action]")
      ?.getAttribute("data-action")
    return { identifiers, actionAttr, buttonActionAttr }
  })
  console.log("Stimulus identifiers:", info.identifiers)
  console.log("Controller attr:", info.actionAttr)
  console.log("Button data-action:", info.buttonActionAttr)
})
