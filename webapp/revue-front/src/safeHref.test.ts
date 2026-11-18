import { toSafeInternalHref } from "./safeHref"

describe("toSafeInternalHref", () => {
  it.each([
    "/data/revue/",
    "/data/revue/cohortes/7?vue=lignes",
    "/data/revue/?a=1&b=2",
    "/admin/login/?next=%2Fdata%2Frevue%2F",
  ])("keeps an internal path: %s", (value) => {
    expect(toSafeInternalHref(`  ${value}  `)).toBe(value)
  })

  it("percent-encodes HTML meta-characters left in the path", () => {
    expect(toSafeInternalHref("/data/revue/foo'bar")).toBe("/data/revue/foo%27bar")
  })

  it.each([
    "",
    "cohortes",
    "//evil.example",
    "/\\evil.example",
    "/\t/evil.example",
    "/\n/evil.example",
    "/\\\\evil.example",
    "https://evil.example",
    "javascript:alert(1)",
    "JavaScript:alert(document.domain)",
    " mailto:hello@example.com",
  ])("replaces an unsafe target with /: %s", (value) => {
    expect(toSafeInternalHref(value)).toBe("/")
  })
})
