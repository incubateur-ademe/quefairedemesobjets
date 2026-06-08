import { computeAvailableHeight } from "../js/helpers"

describe("computeAvailableHeight", () => {
  it("returns the remaining height when there is room", () => {
    expect(computeAvailableHeight(120, 700, 8)).toBe(572)
  })

  it("clamps to zero when the frame top is already past the body bottom", () => {
    expect(computeAvailableHeight(800, 700, 8)).toBe(0)
  })

  it("clamps to zero when the margin alone eats all remaining space", () => {
    expect(computeAvailableHeight(695, 700, 8)).toBe(0)
  })

  it("respects the margin: dropdown bottom stays `margin` px above body", () => {
    const bodyHeight = 220
    const frameTop = 120
    const margin = 8
    const available = computeAvailableHeight(frameTop, bodyHeight, margin)
    expect(frameTop + available).toBe(bodyHeight - margin)
  })

  it("handles a zero margin", () => {
    expect(computeAvailableHeight(120, 700, 0)).toBe(580)
  })
})
