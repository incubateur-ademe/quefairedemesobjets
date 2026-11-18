import { nafLabel } from "./naf"

describe("nafLabel", () => {
  it("gives the label of a sub-class", () => {
    expect(nafLabel("84.11Z")).toBe("Administration publique générale")
    expect(nafLabel("47.11F")).toBe("Hypermarchés")
  })

  it("is undefined for an unknown or empty code", () => {
    expect(nafLabel("00.00X")).toBeUndefined()
    expect(nafLabel("")).toBeUndefined()
  })
})
