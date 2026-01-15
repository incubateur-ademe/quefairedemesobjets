import { expect, test } from "@playwright/test"
import { getIframe, navigateTo, TIMEOUT } from "./helpers"

test.describe("🎛️ Configuration Carte - Paramètre Legacy Bonus", () => {
  test("Le paramètre legacy bonus=1 initialise le filtre bonus comme coché", async ({
    page,
  }) => {
    // Navigate to the test preview page
    await navigateTo(page, "/lookbook/preview/tests/t_9_bonus_legacy_parameter")

    // Wait for the iframe to be loaded
    const iframe = getIframe(page)
    await expect(iframe.locator("body")).toBeAttached({ timeout: TIMEOUT.DEFAULT })

    // Wait for the carte to be loaded
    await iframe
      .locator('[data-testid="carte-adresse-input"]')
      .waitFor({ timeout: TIMEOUT.DEFAULT })

    // Open the filtres modal
    const filtresButton = iframe.locator('[data-modal-open-btn="carte:filtres"]')
    await expect(filtresButton).toBeVisible({ timeout: TIMEOUT.SHORT })
    await filtresButton.click()

    // Wait for modal to open
    const filtresModal = iframe.locator('[data-modal="carte:filtres"]')
    await expect(filtresModal).toBeVisible({ timeout: TIMEOUT.SHORT })

    // Verify that the bonus checkbox is checked
    const bonusCheckbox = iframe.locator('input[name="filtres-bonus"]')
    await expect(bonusCheckbox).toBeChecked({ timeout: TIMEOUT.SHORT })
  })
})

test.describe("🎛️ Configuration Carte - Cacher Filtre Objet", () => {
  test("Une CarteConfig avec cacher_filtre_objet=True masque le filtre objet", async ({
    page,
  }) => {
    // Navigate to the test preview page
    await navigateTo(page, "/lookbook/preview/tests/t_10_cacher_filtre_objet")

    // Wait for the iframe to be loaded
    const iframe = getIframe(page)
    await expect(iframe.locator("body")).toBeAttached({ timeout: TIMEOUT.DEFAULT })

    // Wait for the carte to be loaded
    await iframe
      .locator('[data-testid="carte-adresse-input"]')
      .waitFor({ timeout: TIMEOUT.DEFAULT })

    // Open the filtres modal
    const filtresButton = iframe.locator('[data-modal-open-btn="carte:filtres"]')
    await expect(filtresButton).toBeVisible({ timeout: TIMEOUT.SHORT })
    await filtresButton.click()

    // Wait for modal to open
    const filtresModal = iframe.locator('[data-modal="carte:filtres"]')
    await expect(filtresModal).toBeVisible({ timeout: TIMEOUT.SHORT })

    // Verify that the synonyme field is NOT present in the form
    const synonymeField = iframe.locator('input[name="filtres-synonyme"]')
    await expect(synonymeField).not.toBeAttached()
  })

  test("Une CarteConfig avec paramètres par défaut affiche le filtre objet", async ({
    page,
  }) => {
    // Navigate to the test preview page
    await navigateTo(page, "/lookbook/preview/tests/t_11_default_filtre_objet")

    // Wait for the iframe to be loaded
    const iframe = getIframe(page)
    await expect(iframe.locator("body")).toBeAttached({ timeout: TIMEOUT.DEFAULT })

    // Wait for the carte to be loaded
    await iframe
      .locator('[data-testid="carte-adresse-input"]')
      .waitFor({ timeout: TIMEOUT.DEFAULT })

    // Open the filtres modal
    const filtresButton = iframe.locator('[data-modal-open-btn="carte:filtres"]')
    await expect(filtresButton).toBeVisible({ timeout: TIMEOUT.SHORT })
    await filtresButton.click()

    // Wait for modal to open
    const filtresModal = iframe.locator('[data-modal="carte:filtres"]')
    await expect(filtresModal).toBeVisible({ timeout: TIMEOUT.SHORT })

    // Verify that the synonyme field IS present in the form
    const synonymeField = iframe.locator('input[name="filtres-synonyme"]')
    await expect(synonymeField).toBeAttached({ timeout: TIMEOUT.SHORT })
    await expect(synonymeField).toBeVisible({ timeout: TIMEOUT.SHORT })
  })
})
