import { Application } from "@hotwired/stimulus"
import ComboboxController from "../controllers/assistant/combobox_controller"

// stimulus-use ships as ESM only, which this Jest setup does not transform.
jest.mock("stimulus-use", () => ({ useDebounce: () => {}, useClickOutside: () => {} }))

const RESULTS = [
  { label: "Télécommande", slug: "telecommande" },
  { label: "Téléphone <b>mobile</b>", slug: "telephone" },
]

const settle = () => new Promise((resolve) => setTimeout(resolve, 10))

function type(input: HTMLInputElement, value: string) {
  input.value = value
  input.dispatchEvent(new Event("input", { bubbles: true }))
}

function press(input: HTMLInputElement, key: string): KeyboardEvent {
  const event = new KeyboardEvent("keydown", { key, bubbles: true, cancelable: true })
  input.dispatchEvent(event)
  return event
}

let fetchMock: jest.Mock
let application: Application

function mount({ requireChoice = false, results = RESULTS } = {}) {
  document.body.innerHTML = `
    <div data-controller="assistant-combobox" id="champ"
         data-assistant-combobox-url-value="/api/v1/objets"
         data-assistant-combobox-require-choice-value="${requireChoice}">
      <span data-assistant-combobox-target="cadre"></span>
      <input data-assistant-combobox-target="input"
             data-action="input->assistant-combobox#search
                          keydown->assistant-combobox#navigate">
      <ul data-assistant-combobox-target="list"
          data-action="mousedown->assistant-combobox#keepFocus
                       click->assistant-combobox#chooseFromClick" hidden></ul>
      <input type="hidden" data-assistant-combobox-target="hidden" data-key="slug">
      <input type="hidden" data-assistant-combobox-target="hidden"
             data-key="synonyme" data-optional>
      <p id="champ-aucun" data-assistant-combobox-target="aucunResultat" hidden></p>
    </div>`
  fetchMock = jest.fn(async () => ({ ok: true, json: async () => ({ results }) }))
  global.fetch = fetchMock as unknown as typeof fetch
  application = Application.start()
  application.register("assistant-combobox", ComboboxController)
  return settle()
}

const input = () => document.querySelector("input:not([type])") as HTMLInputElement
const hidden = (key: string) =>
  document.querySelector(`[data-key="${key}"]`) as HTMLInputElement
const noResult = () => document.getElementById("champ-aucun") as HTMLElement

afterEach(() => application.stop())

describe("assistant combobox", () => {
  it("does not search again for the same text", async () => {
    await mount()
    type(input(), "télé")
    await settle()
    const option = document.querySelector('[data-index="1"]') as HTMLElement

    type(input(), "télé")
    await settle()

    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(option.isConnected).toBe(true)
  })

  it("keeps the choice when a late input replays its label", async () => {
    await mount()
    type(input(), "télé")
    await settle()

    ;(document.querySelector('[data-index="0"]') as HTMLElement).click()
    type(input(), "Télécommande")
    await settle()

    expect(input().value).toBe("Télécommande")
    expect(hidden("slug").value).toBe("telecommande")
  })

  it("escapes the labels of the suggestions", async () => {
    await mount()
    type(input(), "télé")
    await settle()

    expect(document.querySelector("[data-index='1'] b")).toBeNull()
  })

  it("flags a query that matches nothing", async () => {
    await mount({ results: [] })
    type(input(), "zzz")
    await settle()

    expect(noResult().hidden).toBe(false)
    expect(input().getAttribute("aria-invalid")).toBe("true")
  })

  it("does not flag a number still being typed", async () => {
    await mount({ results: [] })
    type(input(), "36")
    await settle()

    expect(noResult().hidden).toBe(true)
  })

  it("with a required choice, Enter picks the first suggestion", async () => {
    await mount({ requireChoice: true })
    type(input(), "télé")
    await settle()

    const event = press(input(), "Enter")

    expect(event.defaultPrevented).toBe(true)
    expect(hidden("slug").value).toBe("telecommande")
  })

  it("an optional hidden field does not block a resolved choice", async () => {
    await mount({ requireChoice: true })
    type(input(), "télé")
    await settle()
    ;(document.querySelector('[data-index="0"]') as HTMLElement).click()

    expect(press(input(), "Enter").defaultPrevented).toBe(false)
  })
})
