import { externalLink } from "./externalLinks"

describe("externalLink", () => {
  it.each([
    ["https://www.acteur.fr", "voir le site", "https://www.acteur.fr"],
    ["http://acteur.org/page", "voir le site", "http://acteur.org/page"],
    [
      "123 456 789 00012",
      "voir dans AE",
      "https://annuaire-entreprises.data.gouv.fr/etablissement/12345678900012",
    ],
    [
      "123456789",
      "voir dans AE",
      "https://annuaire-entreprises.data.gouv.fr/entreprise/123456789",
    ],
  ])("%s", (value, label, href) => {
    expect(externalLink(value)).toMatchObject({ label, href })
  })

  it.each(["", null, "acteur.fr", "12345", "1234567890", "javascript:alert(1)"])(
    "no link for %p",
    (value) => {
      expect(externalLink(value)).toBeNull()
    },
  )
})
