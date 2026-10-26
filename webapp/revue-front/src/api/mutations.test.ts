import { groupe, ligne } from "../screens/cohorte/fixtures"
import { withProposition, withReport, withRestauration, withStatut } from "./mutations"

describe("optimistic updates", () => {
  it("decides the whole groupe and disables its actions", () => {
    const next = withStatut(groupe(1), "ATRAITER")

    expect(next.statut).toBe("ATRAITER")
    expect(next.lignes.map((l) => l.statut)).toEqual(["ATRAITER", "ATRAITER"])
    expect(next.lignes_validees).toBe(2)
    expect(next.capacites.valider).toBe(false)
  })

  it("decides one ligne only", () => {
    const next = withStatut(groupe(1), "ATRAITER", ["1:nom"])

    expect(next.statut).toBe("AVALIDER")
    expect(next.lignes.map((l) => l.statut)).toEqual(["ATRAITER", "AVALIDER"])
    expect(next.capacites.valider).toBe(true)
  })

  it("reports the suggestion of the source on reportable lignes", () => {
    const base = groupe(1, {
      lignes: [
        ligne(1, ["nom"]),
        ligne(1, ["identifiant_unique"], {
          capacites: { ...ligne(1, ["x"]).capacites, reporter_correction: false },
        }),
      ],
    })

    const next = withReport(base, "RevisionActeur")

    expect(next.lignes[0].correction.propose).toEqual({ nom: "nom source" })
    expect(next.lignes[1].correction.propose).toBeNull()
  })

  it("sets and removes a proposition", () => {
    const set = withProposition(groupe(1), "1:url", "RevisionActeur", {
      url: "https://a.fr",
    })
    expect(set.lignes[1].correction.propose).toEqual({ url: "https://a.fr" })
    expect(
      withProposition(set, "1:url", "RevisionActeur", null).lignes[1].correction
        .propose,
    ).toBeNull()
  })

  it("restores the value of the acteur, « __empty__ » when it is empty", () => {
    const restorable = { ...ligne(1, ["x"]).capacites, restaurer_correction: true }
    const base = groupe(1, {
      lignes: [
        ligne(1, ["nom"], { capacites: restorable }),
        ligne(1, ["url"], {
          capacites: restorable,
          acteur: {
            actuel: { url: "" },
            propose: { url: "https://a.fr" },
            etat: "valeur",
          },
        }),
        ligne(1, ["siret"]),
      ],
    })

    const next = withRestauration(base)

    expect(next.lignes[0].correction.propose).toEqual({ nom: "nom actuel" })
    expect(next.lignes[1].correction.propose).toEqual({ url: "__empty__" })
    expect(next.lignes[2].correction.propose).toBeNull()
    expect(withRestauration(base, ["1:url"]).lignes[0].correction.propose).toBeNull()
  })
})
