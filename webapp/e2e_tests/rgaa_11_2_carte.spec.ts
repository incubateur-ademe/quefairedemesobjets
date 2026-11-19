import { expect } from "@playwright/test"
import { test } from "./fixtures"
import { mockApiAdresse, navigateTo, openModal, searchForAuray } from "./helpers"

test.use({ locale: "fr-FR" })

test.describe("♿ RGAA 11.2 — Étiquettes de champs de la carte", () => {
  test("les champs facultatifs des filtres sont marqués en français", async ({
    page,
  }) => {
    await navigateTo(page, `/carte`)
    await mockApiAdresse(page)
    await searchForAuray(page)
    await openModal(page, {
      parentTestId: "carte-legend",
      buttonDataTestId: "modal-button-carte:filtres",
      modalDataTestId: "modal-carte:filtres",
      closeModal: false,
    })

    const modal = page.getByTestId("modal-carte:filtres")
    await expect(modal).toBeVisible()
    await expect(modal).toContainText("(Optionnel)")
    await expect(modal).not.toContainText("(Optional)")
  })
})
