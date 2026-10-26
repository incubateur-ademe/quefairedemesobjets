import { scrollRowIntoView, scrollRowToTop } from "./scroll"

function layout(rowTop: number, rowHeight: number) {
  document.body.innerHTML = `<div class="scroll"><table><thead><tr><th>h</th></tr></thead>
    <tbody><tr id="row"><td>x</td></tr></tbody></table></div>`
  const container = document.querySelector(".scroll") as HTMLElement
  const box = (top: number, height: number) =>
    ({ top, bottom: top + height, height }) as DOMRect
  container.getBoundingClientRect = () => box(100, 400)
  document.querySelector("thead")!.getBoundingClientRect = () => box(100, 40)
  document.querySelector("#row")!.getBoundingClientRect = () => box(rowTop, rowHeight)
  container.scrollTop = 1000
  return container
}

describe("scrollRowIntoView", () => {
  it("shows a row hidden under the sticky header", () => {
    const container = layout(110, 30)
    scrollRowIntoView(document.querySelector("#row"))
    expect(container.scrollTop).toBe(1000 - 30)
  })

  it("shows a row below the visible area", () => {
    const container = layout(480, 50)
    scrollRowIntoView(document.querySelector("#row"))
    expect(container.scrollTop).toBe(1000 + 30)
  })

  it("does not move a visible row", () => {
    const container = layout(200, 30)
    scrollRowIntoView(document.querySelector("#row"))
    expect(container.scrollTop).toBe(1000)
  })
})

describe("scrollRowToTop", () => {
  it("places a row below the sticky header", () => {
    const container = layout(300, 30)
    const scrollTo = jest.spyOn(container, "scrollTo")
    scrollRowToTop(document.querySelector("#row"))
    expect(scrollTo).toHaveBeenCalledWith({ top: 1000 + 160, behavior: "smooth" })
  })

  it("places a row hidden under the sticky header", () => {
    const container = layout(110, 30)
    scrollRowToTop(document.querySelector("#row"))
    expect(container.scrollTop).toBe(1000 - 30)
  })
})
