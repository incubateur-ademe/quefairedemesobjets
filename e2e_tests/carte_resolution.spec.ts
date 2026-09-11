import { expect, test } from "@playwright/test"

test.describe("🗺️ Check display of Carte according to resolutions", () => {
  const smallResolutions = [
    { width: 350, height: 700 },
    { width: 800, height: 700 },
  ]
  const largeResolutions = [
    { width: 1024, height: 900 },
    { width: 1400, height: 900 },
  ]
  const RESOLUTIONS = [...smallResolutions, ...largeResolutions]
  test.describe("Check inputs Carte/Liste", () => {
    for (const resolution of RESOLUTIONS) {
      test(`Inputs Carte/Liste à ${resolution.width}x${resolution.height}`, async ({
        page,
      }) => {
        await page.setViewportSize({
          width: resolution.width,
          height: resolution.height,
        })
        await page.goto(`/carte`, {
          waitUntil: "domcontentloaded",
        })

        // Vérifier que l'input "Carte" est checked
        const inputCarte = page.getByRole("radio", { name: "Carte" })
        await expect(inputCarte).toBeChecked()

        // Vérifier que l'input "Liste" n'est pas checked
        const inputListe = page.getByRole("radio", { name: "Liste" })
        await expect(inputListe).not.toBeChecked()
      })
    }
  })

  test.describe("Check logo visibility", () => {
    const smallResolutions = [
      { width: 350, height: 700 },
      { width: 800, height: 700 },
    ]
    const largeResolutions = [
      { width: 1024, height: 900 },
      { width: 1400, height: 900 },
    ]

    for (const resolution of smallResolutions) {
      test(`Logo should not be visible at ${resolution.width}x${resolution.height}`, async ({
        page,
      }) => {
        await page.setViewportSize({
          width: resolution.width,
          height: resolution.height,
        })
        await page.goto(`/carte`, {
          waitUntil: "domcontentloaded",
        })

        const logo = page.locator("#logo")
        await expect(logo).toBeHidden()
      })
    }

    for (const resolution of largeResolutions) {
      test(`Logo should be visible at ${resolution.width}x${resolution.height}`, async ({
        page,
      }) => {
        await page.setViewportSize({
          width: resolution.width,
          height: resolution.height,
        })
        await page.goto(`/carte`, {
          waitUntil: "domcontentloaded",
        })

        const logo = page.locator("#logo")
        await expect(logo).toBeVisible()
      })
    }
  })

  test.describe("Check filter button visibility", () => {
    const smallResolutions = [
      { width: 350, height: 700 },
      { width: 800, height: 700 },
    ]
    const largeResolutions = [
      { width: 1024, height: 900 },
      { width: 1400, height: 900 },
    ]

    for (const resolution of smallResolutions) {
      test(`Filter button should be visible at ${resolution.width}x${resolution.height}`, async ({
        page,
      }) => {
        await page.setViewportSize({
          width: resolution.width,
          height: resolution.height,
        })
        await page.goto(`/carte`, {
          waitUntil: "domcontentloaded",
        })

        const filterButton = page.getByTestId("modal-button-carte:filtres")
        await expect(filterButton).toBeVisible()
      })
    }

    for (const resolution of largeResolutions) {
      test(`Filter button should not be visible at ${resolution.width}x${resolution.height}`, async ({
        page,
      }) => {
        await page.setViewportSize({
          width: resolution.width,
          height: resolution.height,
        })
        await page.goto(`/carte`, {
          waitUntil: "domcontentloaded",
        })

        const filterButton = page.getByTestId("modal-button-carte:filtres")
        await expect(filterButton).toBeHidden()
      })
    }
  })
})
