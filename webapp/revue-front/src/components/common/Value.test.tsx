import { render } from "@testing-library/react"

import { DiffValue, diffSegments } from "./Value"

describe("diffSegments", () => {
  it("keeps the common parts, like the admin", () => {
    expect(diffSegments("12 rue de la Paix", "12 rue de la Pais")).toEqual([
      ["equal", "12 rue de la Pai"],
      ["removed", "x"],
      ["added", "s"],
    ])
  })
})

describe("DiffValue", () => {
  const html = (actuel: string | null, propose: string | null) =>
    render(<DiffValue actuel={actuel} propose={propose} empty="—" />).container
      .innerHTML

  it("strikes the removed parts and highlights the added parts", () => {
    expect(html("Paris", "Pariss")).toBe('<span class="val">Paris<ins>s</ins></span>')
  })

  it("highlights the whole proposition without current value", () => {
    expect(html(null, "Lyon")).toBe('<span class="val"><ins>Lyon</ins></span>')
  })

  it("strikes the current value of an emptied field", () => {
    expect(html("Lyon", "")).toBe(
      '<span class="val"><del>Lyon</del></span><span class="empty"> vide</span>',
    )
  })

  it("shows an unchanged value as is", () => {
    expect(html("Lyon", "Lyon")).toBe('<span class="val ">Lyon</span>')
  })
})
