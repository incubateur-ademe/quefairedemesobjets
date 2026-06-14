import { execSync } from "node:child_process"
import { expect, Page } from "@playwright/test"
import { test } from "./fixtures"
import { navigateTo, TIMEOUT } from "./helpers"

/**
 * E2E coverage for the cohorte review screen (data:cohorte_review).
 *
 * The screen is a virtualized TanStack grid driven by a single Stimulus
 * controller, with a grid mode and a focus mode. These tests cover the full
 * feature surface and guard the behaviours that browser testing caught
 * regressing silently (row selection, optimistic decisions, focus restore).
 *
 * Data is seeded by `seed_review_e2e`: a deterministic, self-contained
 * cohorte of 24 groupes (so it works against an empty sample DB). Scheme:
 *   - 20 « à valider », 2 « à traiter », 2 « rejetées » (decided ones last)
 *   - nom + telephone on every groupe; url on even indices (10 à valider)
 *   - telephone starts with « 07 » on index % 3 == 0 (7 à valider)
 *   - 4 « à valider » ids contain « morbihan » (search test)
 */

const NB_AVALIDER = 20
const NB_TEL_07 = 7
const NB_URL = 10
const NB_MORBIHAN = 4

let cohorteId: string

// Reseed before each test: the suite runs serially against a shared sample
// DB and the tests mutate suggestion statuts, so a deterministic starting
// state per test is required for the exact-count assertions.
function seedReviewCohorte() {
  const databaseUrl = process.env.SAMPLE_DATABASE_URL ?? process.env.DATABASE_URL ?? ""
  const output = execSync("uv run python manage.py seed_review_e2e", {
    encoding: "utf-8",
    env: { ...process.env, DATABASE_URL: databaseUrl },
  })
  const match = output.match(/COHORTE_ID=(\d+)/)
  if (!match) {
    throw new Error(`seed_review_e2e did not report a cohorte id:\n${output}`)
  }
  cohorteId = match[1]
}

async function loginAsAdmin(page: Page) {
  await navigateTo(page, "/admin/login/")
  await page.locator('input[name="username"]').fill("admin")
  await page.locator('input[name="password"]').fill("admin")
  await page.locator('[type="submit"]').click()
  await page.waitForURL("**/admin/")
}

async function openReview(page: Page, query = "") {
  await navigateTo(page, `/data/cohorte/${cohorteId}/review/${query}`)
  await expect(page.locator(".status")).not.toHaveText("Chargement…", {
    timeout: TIMEOUT.DEFAULT,
  })
}

const bulkReject = 'sl-button[data-action="click->cohorte-review#bulkReject"]'
const bulkAccept = 'sl-button[data-action="click->cohorte-review#bulkAccept"]'
const applyBuilder = 'sl-button[data-action="click->cohorte-review#vbApply"]'

// sl-input / sl-select are web components: set the value and fire the event
// the controller listens for (Playwright's fill() can't reach the shadow input).
async function setShoelaceValue(page: Page, selector: string, value: string) {
  await page
    .locator(selector)
    .evaluate((el: HTMLInputElement & { value: string }, v) => {
      el.value = v
      el.dispatchEvent(new Event("sl-input", { bubbles: true }))
      el.dispatchEvent(new Event("sl-change", { bubbles: true }))
    }, value)
}

// ---------------------------------------------------------------------------
// Access control
// ---------------------------------------------------------------------------

test.describe("🔒 Revue de cohorte — accès", () => {
  test.beforeAll(() => seedReviewCohorte())

  test("un utilisateur anonyme est redirigé vers la connexion", async ({ page }) => {
    await navigateTo(page, `/data/cohorte/${cohorteId}/review/`)
    await expect(page).toHaveURL(/\/admin\/login/)
  })
})

// ---------------------------------------------------------------------------
// Grid mode
// ---------------------------------------------------------------------------

test.describe("🗂️ Revue de cohorte — grille", () => {
  test.beforeEach(async ({ page }) => {
    seedReviewCohorte()
    await loginAsAdmin(page)
  })

  test("la grille pivot charge les acteurs et leurs champs", async ({ page }) => {
    await openReview(page)

    await expect(page.locator("tbody tr[data-groupe-id]").first()).toBeVisible({
      timeout: TIMEOUT.DEFAULT,
    })
    await expect(page.locator('thead .focus-entry[data-field="nom"]')).toBeVisible()
    await expect(
      page.locator('thead .focus-entry[data-field="telephone"]'),
    ).toBeVisible()
    await expect(page.locator('thead .focus-entry[data-field="url"]')).toBeVisible()
    // default filter is « à valider »
    await expect(page.locator(".status")).toContainText(`/ ${NB_AVALIDER} acteurs`)
  })

  test("accepter une cellule la marque acceptée (UI optimiste)", async ({ page }) => {
    await openReview(page)

    const cell = page.locator("td.sug.pending").first()
    await expect(cell).toBeVisible({ timeout: TIMEOUT.DEFAULT })
    await cell.locator(".cell-action.accept").click()

    await expect(page.locator("td.sug.accepted").first()).toBeVisible({
      timeout: TIMEOUT.SHORT,
    })
  })

  test("rejeter puis réinitialiser une cellule (↺)", async ({ page }) => {
    await openReview(page)

    const cell = page.locator("td.sug.pending").first()
    await expect(cell).toBeVisible({ timeout: TIMEOUT.DEFAULT })
    await cell.locator(".cell-action.reject").click()
    await expect(page.locator("td.sug.rejected").first()).toBeVisible({
      timeout: TIMEOUT.SHORT,
    })

    // a decided cell exposes the reset action
    await page.locator("td.sug.rejected").first().locator(".cell-action.reset").click()
    await expect(page.locator("td.sug.rejected")).toHaveCount(0, {
      timeout: TIMEOUT.SHORT,
    })
  })

  test("masquer puis réafficher une colonne", async ({ page }) => {
    await openReview(page)
    const urlHeader = page.locator('thead th:has(.focus-entry[data-field="url"])')
    await expect(urlHeader).toBeVisible({ timeout: TIMEOUT.DEFAULT })

    const toggle = page.locator('sl-button[data-field-toggle="url"]')
    await toggle.click()
    await expect(urlHeader).toBeHidden()
    await toggle.click()
    await expect(urlHeader).toBeVisible()
  })

  test("recherche par identifiant acteur", async ({ page }) => {
    await openReview(page)
    await expect(page.locator("tbody tr[data-groupe-id]").first()).toBeVisible({
      timeout: TIMEOUT.DEFAULT,
    })

    await setShoelaceValue(page, ".search", "morbihan")
    await expect(page.locator(".status")).toContainText(`/ ${NB_MORBIHAN} acteurs`, {
      timeout: TIMEOUT.DEFAULT,
    })
  })

  test("filtre par statut", async ({ page }) => {
    await openReview(page)
    await expect(page.locator(".status")).toContainText(`/ ${NB_AVALIDER} acteurs`, {
      timeout: TIMEOUT.DEFAULT,
    })

    await page.locator(".statut-filter").evaluate((el: HTMLSelectElement) => {
      el.value = "REJETEE"
      el.dispatchEvent(new Event("sl-change", { bubbles: true }))
    })
    await expect(page.locator(".status")).toContainText("/ 2 acteurs", {
      timeout: TIMEOUT.DEFAULT,
    })
  })

  test("recherche et statut sont conservés dans l'URL au rechargement", async ({
    page,
  }) => {
    await openReview(page)
    await setShoelaceValue(page, ".search", "morbihan")
    await expect(page.locator(".status")).toContainText(`/ ${NB_MORBIHAN} acteurs`, {
      timeout: TIMEOUT.DEFAULT,
    })

    await expect(page).toHaveURL(/q=morbihan/)
    await page.reload()
    await expect(page.locator(".status")).toContainText(`/ ${NB_MORBIHAN} acteurs`, {
      timeout: TIMEOUT.DEFAULT,
    })
  })

  test("sélection multi-lignes : accepter en masse", async ({ page }) => {
    await openReview(page)
    const rows = page.locator("tbody tr[data-groupe-id]")
    await expect(rows.first()).toBeVisible({ timeout: TIMEOUT.DEFAULT })

    await rows.nth(0).locator("sl-checkbox").click()
    await rows.nth(1).locator("sl-checkbox").click()
    await expect(page.locator('[data-cohorte-review-target="bulkCount"]')).toHaveText(
      "2",
    )

    await page.locator(bulkAccept).click()
    await expect(page.locator("td.sug.accepted").first()).toBeVisible({
      timeout: TIMEOUT.SHORT,
    })
  })

  test("sélection multi-lignes : rejet de masse, avec annulation", async ({ page }) => {
    await openReview(page)
    const rows = page.locator("tbody tr[data-groupe-id]")
    await expect(rows.first()).toBeVisible({ timeout: TIMEOUT.DEFAULT })

    await rows.nth(0).locator("sl-checkbox").click()
    await rows.nth(1).locator("sl-checkbox").click()
    await page.locator(bulkReject).click()

    const toast = page.locator(".undo-toast")
    await expect(toast).toBeVisible({ timeout: TIMEOUT.SHORT })
    await expect(toast).toContainText("rejetée")

    await page.locator(".undo-toast-action").click()
    await expect(toast).toBeHidden({ timeout: TIMEOUT.SHORT })
    await expect(page.locator('[data-cohorte-review-target="announcer"]')).toHaveText(
      "Action annulée",
    )
    await expect(page.locator("td.sug.rejected")).toHaveCount(0)
  })

  test("« sélectionner tous les filtrés » sauf des lignes cochées", async ({
    page,
  }) => {
    await openReview(page)
    const rows = page.locator("tbody tr[data-groupe-id]")
    await expect(rows.first()).toBeVisible({ timeout: TIMEOUT.DEFAULT })

    // exclude the first two rows, then act on all filtered minus those
    await rows.nth(0).locator("sl-checkbox").click()
    await rows.nth(1).locator("sl-checkbox").click()
    await page.locator('[data-cohorte-review-target="selectFiltered"]').click()
    await expect(
      page.locator('[data-cohorte-review-target="bulkCount"]'),
    ).toContainText(`${NB_AVALIDER - 2}`)

    // accept the filtered set; the confirm dialog carries the net count
    page.once("dialog", (dialog) => {
      expect(dialog.message()).toContain(`${NB_AVALIDER - 2}`)
      dialog.accept()
    })
    await page.locator(bulkAccept).click()

    // after a filter-scope action the grid reloads: the 2 excluded rows
    // remain « à valider », so they are still shown under the default filter
    await expect(page.locator(".status")).toContainText("/ 2 acteurs", {
      timeout: TIMEOUT.DEFAULT,
    })
  })

  test("le pager rapporte honnêtement chargés / total", async ({ page }) => {
    // 24 groupes fit in one batch (limit 100); the cursor pagination itself is
    // covered by unit tests. Assert the honest « N sur total » readout.
    await openReview(page)
    await expect(
      page.locator('[data-cohorte-review-target="pagerInfo"]'),
    ).toContainText(`sur ${NB_AVALIDER}`, { timeout: TIMEOUT.DEFAULT })
  })
})

// ---------------------------------------------------------------------------
// Focus mode
// ---------------------------------------------------------------------------

test.describe("🎯 Revue de cohorte — mode focus", () => {
  test.beforeEach(async ({ page }) => {
    seedReviewCohorte()
    await loginAsAdmin(page)
  })

  test("le badge 🎯 d'une colonne ouvre le mode focus", async ({ page }) => {
    await openReview(page)
    await page.locator('thead .focus-entry[data-field="telephone"]').click()

    await expect(page).toHaveURL(/\?focus=telephone/)
    await expect(page.locator(".focus-layout")).toBeVisible({
      timeout: TIMEOUT.DEFAULT,
    })
    await expect(page.locator(".focus-card.active")).toHaveCount(1)
  })

  test("revue au clavier : ↓ navigue, A accepte, R rejette, U annule", async ({
    page,
  }) => {
    await openReview(page, "?focus=telephone")
    const cards = page.locator(".focus-card")
    await expect(cards.first()).toBeVisible({ timeout: TIMEOUT.DEFAULT })
    const initialCount = await cards.count()

    await page.locator(".focus-cards").focus()
    // accept the first, advance, reject the second
    await page.keyboard.press("a")
    await expect(page.locator(".focus-card.accepted")).toHaveCount(1, {
      timeout: TIMEOUT.SHORT,
    })
    await page.keyboard.press("r")
    await expect(page.locator(".focus-card.rejected")).toHaveCount(1, {
      timeout: TIMEOUT.SHORT,
    })

    // navigate back up and undo the first decision
    await page.keyboard.press("ArrowUp")
    await page.keyboard.press("ArrowUp")
    await page.keyboard.press("u")
    await expect(page.locator(".focus-card.accepted")).toHaveCount(0, {
      timeout: TIMEOUT.SHORT,
    })

    // decided rows stay in place: total unchanged, one cursor
    await expect(cards).toHaveCount(initialCount)
    await expect(page.locator(".focus-card.active")).toHaveCount(1)
  })

  test("le query builder filtre par valeur suggérée", async ({ page }) => {
    await openReview(page, "?focus=telephone")
    await expect(page.locator(".focus-card").first()).toBeVisible({
      timeout: TIMEOUT.DEFAULT,
    })

    await page.locator(".vb-row .vb-value").first().fill("07")
    await page.locator(applyBuilder).click()

    await expect(page.locator(".vb-active")).toContainText("filtre actif", {
      timeout: TIMEOUT.SHORT,
    })
    await expect(page.locator(".focus-card")).toHaveCount(NB_TEL_07)
  })

  test("query builder à deux groupes combinés (07 OU 02 99 05)", async ({ page }) => {
    await openReview(page, "?focus=telephone")
    await expect(page.locator(".focus-card").first()).toBeVisible({
      timeout: TIMEOUT.DEFAULT,
    })

    // group 1: commence par 07
    await page.locator(".vb-row .vb-value").first().fill("07")
    // add a second group: commence par 02 99 05 (matches index 05 → "02 99 05…")
    await page.locator('button[data-action="click->cohorte-review#vbAddGroup"]').click()
    await page.locator(".vb-group").nth(1).locator(".vb-value").fill("02 99 05")
    await page.locator(applyBuilder).click()

    await expect(page.locator(".vb-active")).toContainText("filtre actif", {
      timeout: TIMEOUT.SHORT,
    })
    // 7 starting with 07 (à valider) + index 05 = 8
    await expect(page.locator(".focus-card")).toHaveCount(NB_TEL_07 + 1)
  })

  test("« Accepter les N filtrées » agit sur tout l'ensemble filtré", async ({
    page,
  }) => {
    await openReview(page, "?focus=telephone")
    await expect(page.locator(".focus-card").first()).toBeVisible({
      timeout: TIMEOUT.DEFAULT,
    })

    await page.locator(".vb-row .vb-value").first().fill("07")
    await page.locator(applyBuilder).click()
    await expect(page.locator(".focus-card")).toHaveCount(NB_TEL_07)

    page.once("dialog", (dialog) => {
      expect(dialog.message()).toContain(`${NB_TEL_07}`)
      dialog.accept()
    })
    await page
      .locator('sl-button[data-action="click->cohorte-review#focusBulkAccept"]')
      .click()

    // those 7 telephone fields are now decided → no longer à valider
    await expect(page.locator(".focus-card")).toHaveCount(0, {
      timeout: TIMEOUT.DEFAULT,
    })
  })

  test("changer de champ via le rail sans quitter le mode focus", async ({ page }) => {
    await openReview(page, "?focus=telephone")
    await expect(page.locator(".focus-layout")).toBeVisible({
      timeout: TIMEOUT.DEFAULT,
    })

    await page.locator('.field-item[data-field="url"]').click()
    await expect(page).toHaveURL(/\?focus=url/)
    await expect(page.locator(".focus-card")).toHaveCount(NB_URL, {
      timeout: TIMEOUT.DEFAULT,
    })
  })

  test("ouvre le tiroir d'un acteur et agit sur tous ses champs", async ({ page }) => {
    await openReview(page, "?focus=telephone")
    await expect(page.locator(".focus-card").first()).toBeVisible({
      timeout: TIMEOUT.DEFAULT,
    })

    await page.locator(".focus-cards").focus()
    await page.keyboard.press("Enter")

    const drawer = page.locator(".groupe-drawer")
    await expect(drawer).toHaveAttribute("open", "", { timeout: TIMEOUT.SHORT })
    // the drawer shows every field of the acteur, not just telephone
    await expect(page.locator(".drawer-field").first()).toBeVisible()

    await page
      .locator('.drawer-field:has(th:text-is("nom")) .cell-action.accept')
      .click()
    await expect(page.locator('.drawer-field:has(th:text-is("nom"))')).toHaveClass(
      /accepted/,
      { timeout: TIMEOUT.SHORT },
    )

    // Escape closes the drawer but stays in focus mode (two-step)
    await page.keyboard.press("Escape")
    await expect(drawer).not.toHaveAttribute("open", "")
    await expect(page).toHaveURL(/\?focus=telephone/)
    await expect(page.locator(".focus-layout")).toBeVisible()
  })

  test("le tiroir : « tout accepter » décide tous les champs", async ({ page }) => {
    await openReview(page, "?focus=telephone")
    await expect(page.locator(".focus-card").first()).toBeVisible({
      timeout: TIMEOUT.DEFAULT,
    })

    await page.locator(".focus-cards").focus()
    await page.keyboard.press("Enter")
    await expect(page.locator(".groupe-drawer")).toHaveAttribute("open", "", {
      timeout: TIMEOUT.SHORT,
    })

    await page
      .locator('sl-button[data-action="click->cohorte-review#drawerAcceptAll"]')
      .click()
    await expect(page.locator(".drawer-field.pending")).toHaveCount(0, {
      timeout: TIMEOUT.SHORT,
    })
  })

  test("Échap quitte le mode focus", async ({ page }) => {
    await openReview(page, "?focus=telephone")
    await expect(page.locator(".focus-layout")).toBeVisible({
      timeout: TIMEOUT.DEFAULT,
    })

    await page.keyboard.press("Escape")

    await expect(page).not.toHaveURL(/\?focus=/)
    await expect(page.locator(".focus-layout")).toBeHidden()
    await expect(page.locator(".table-wrap")).toBeVisible()
  })
})
