import "@testing-library/jest-dom"

import { Application } from "@hotwired/stimulus"
import SearchFormController from "../controllers/carte/search_solution_form_controller"

// Minimal carte form: a `carte` target marks it as carte mode, plus the hidden
// lat/lon/bbox inputs the controller reads/writes. We spy on requestSubmit
// because jsdom does not implement form submission.
function setupForm(latValue = "", lonValue = "", { withCarteTarget = true } = {}) {
  document.body.innerHTML = `
    <form data-controller="search-solution-form"
          data-action="qf:location-changed@document->search-solution-form#applyLocationChange">
      ${withCarteTarget ? '<div data-search-solution-form-target="carte"></div>' : ""}
      <input name="carte_map-adresse" value="">
      <input data-search-solution-form-target="latitudeInput" value="${latValue}">
      <input data-search-solution-form-target="longitudeInput" value="${lonValue}">
      <input data-search-solution-form-target="bbox" value='{"stale":true}'>
    </form>`
  const form = document.querySelector("form") as HTMLFormElement
  const requestSubmit = jest.fn()
  form.requestSubmit = requestSubmit
  return { form, requestSubmit }
}

let app: Application | undefined

function startStimulus() {
  app = Application.start()
  app.register("search-solution-form", SearchFormController)
  return app
}

async function flush() {
  await new Promise((r) => setTimeout(r, 0))
}

function getInput(form: HTMLFormElement, target: string): HTMLInputElement {
  return form.querySelector(
    `[data-search-solution-form-target="${target}"]`,
  ) as HTMLInputElement
}

describe("SearchFormController location hydration", () => {
  beforeEach(() => {
    sessionStorage.clear()
    document.body.innerHTML = ""
  })

  afterEach(() => {
    app?.stop()
    app = undefined
  })

  describe("#hydrateOnConnect (eager cold-load)", () => {
    it("submits once when sessionStorage has coords and inputs are empty", async () => {
      sessionStorage.setItem("latitude", "47.66")
      sessionStorage.setItem("longitude", "-2.99")
      sessionStorage.setItem("adresse", "Auray")
      const { form, requestSubmit } = setupForm("", "")
      startStimulus()
      await flush()

      expect(getInput(form, "latitudeInput").value).toBe("47.66")
      expect(getInput(form, "longitudeInput").value).toBe("-2.99")
      expect(
        (form.querySelector('input[name$="_map-adresse"]') as HTMLInputElement).value,
      ).toBe("Auray")
      expect(getInput(form, "bbox").value).toBe("") // stale bbox reset
      expect(requestSubmit).toHaveBeenCalledTimes(1)
    })

    it("does NOT submit when inputs are already populated (server-source)", async () => {
      sessionStorage.setItem("latitude", "47.66")
      sessionStorage.setItem("longitude", "-2.99")
      const { requestSubmit } = setupForm("47.66", "-2.99")
      startStimulus()
      await flush()

      expect(requestSubmit).not.toHaveBeenCalled()
    })

    it("does NOT submit when sessionStorage has no complete location", async () => {
      sessionStorage.setItem("latitude", "47.66") // missing longitude
      const { requestSubmit } = setupForm("", "")
      startStimulus()
      await flush()

      expect(requestSubmit).not.toHaveBeenCalled()
    })

    it("does NOT submit when there is no carte target (formulaire)", async () => {
      sessionStorage.setItem("latitude", "47.66")
      sessionStorage.setItem("longitude", "-2.99")
      const { requestSubmit } = setupForm("", "", { withCarteTarget: false })
      startStimulus()
      await flush()

      expect(requestSubmit).not.toHaveBeenCalled()
    })
  })

  describe("applyLocationChange (qf:location-changed)", () => {
    it("writes coords, resets bbox, and submits once", async () => {
      const { form, requestSubmit } = setupForm("", "")
      startStimulus()
      await flush()
      requestSubmit.mockClear() // ignore any connect-time submit

      document.dispatchEvent(
        new CustomEvent("qf:location-changed", {
          detail: { adresse: "Auray", latitude: "47.66", longitude: "-2.99" },
        }),
      )

      expect(getInput(form, "latitudeInput").value).toBe("47.66")
      expect(getInput(form, "longitudeInput").value).toBe("-2.99")
      expect(
        (form.querySelector('input[name$="_map-adresse"]') as HTMLInputElement).value,
      ).toBe("Auray")
      expect(getInput(form, "bbox").value).toBe("")
      expect(requestSubmit).toHaveBeenCalledTimes(1)
    })
  })
})
