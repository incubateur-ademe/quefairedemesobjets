import { coveredHeight, scrollIframeIntoView } from "../js/iframe_scroll"

function rect(top: number, bottom = top + 100): DOMRect {
  return { top, bottom } as DOMRect
}

let header: HTMLElement
let iframe: HTMLElement

beforeEach(() => {
  jest.useFakeTimers()
  document.body.innerHTML = `<header></header><div><iframe></iframe></div>`
  header = document.querySelector("header")!
  iframe = document.querySelector("iframe")!
  header.style.position = "fixed"
  header.getBoundingClientRect = () => rect(0, 80)
  document.elementsFromPoint = () => [header]
  Object.defineProperty(window, "innerHeight", { value: 1000, configurable: true })
  window.scrollTo = jest.fn() as unknown as typeof window.scrollTo
})

afterEach(() => jest.useRealTimers())

test("measures what the host pins to the top of the viewport", () => {
  expect(coveredHeight(iframe)).toBe(80)
})

test("an element containing the iframe does not cover it", () => {
  const container = iframe.parentElement!
  container.style.position = "sticky"
  container.getBoundingClientRect = () => rect(0, 500)
  document.elementsFromPoint = () => [container]

  expect(coveredHeight(iframe)).toBe(0)
})

test("scrolls the iframe just below the fixed header", () => {
  iframe.getBoundingClientRect = () => rect(600)

  expect(scrollIframeIntoView(iframe)).toBe(false)

  expect(window.scrollTo).toHaveBeenCalledWith({
    top: window.scrollY + 600 - (80 + 16),
    behavior: "smooth",
  })
})

test("leaves an iframe already visible below the header", () => {
  iframe.getBoundingClientRect = () => rect(120)

  scrollIframeIntoView(iframe)

  expect(window.scrollTo).not.toHaveBeenCalled()
})
