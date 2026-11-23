import { fireEvent, screen, waitFor, within } from "@testing-library/react"

import type { LignePage } from "../../api/types"
import { fakeApi, renderApp } from "../../test-utils"
import { CohorteScreen } from "./CohorteScreen"
import { COHORTE, groupe, ligne, STATS } from "./fixtures"

const LIGNES: LignePage = {
  items: [
    { groupe_id: 1, key: "1:nom" },
    { groupe_id: 1, key: "1:url" },
    { groupe_id: 2, key: "2:url" },
  ],
  groupes: [groupe(1), groupe(2)],
  total: 3,
  page: 1,
  page_size: 500,
}

function setup(url = "/data/revue/cohortes/7?vue=lignes") {
  const api = fakeApi((path, _options, method) => {
    if (method !== "GET") {
      // The server answers with the groupe, its ligne « url » validated
      const g = groupe(1)
      return {
        ...g,
        lignes: g.lignes.map((l) =>
          l.key === "1:url" ? { ...l, statut: "ATRAITER" } : l,
        ),
      }
    }
    if (path.endsWith("/stats"))
      return { ...STATS, compteurs: { ...STATS.compteurs, AVALIDER: 3 } }
    if (path.endsWith("/taches")) return []
    if (path.endsWith("/champs/choix")) return {}
    if (path.endsWith("/revue/filtres")) return { champs: [] }
    if (path.endsWith("/lignes")) return LIGNES
    if (path.endsWith("/groupes")) throw new Error("the groupes page is not loaded")
    return COHORTE
  })
  renderApp(<CohorteScreen cohorteId={7} />, { api, url })
  return api
}

const row = (key: string) =>
  document.querySelector(`[data-cursor="l:${key}"]`) as HTMLElement

describe("LignesView", () => {
  it("shows one row per ligne with its groupe and acteur", async () => {
    const api = setup()

    await waitFor(() => expect(row("2:url")).toBeInTheDocument())
    expect(within(row("1:nom")).getByText("1")).toBeInTheDocument()
    expect(within(row("2:url")).getByText("Acteur 2")).toBeInTheDocument()
    expect(within(row("2:url")).getByText("acteur_2")).toBeInTheDocument()
    expect(screen.getByText(/lignes 1–3 sur 3/)).toBeInTheDocument()
    expect(screen.getByTitle(/^Lignes du filtre/)).toBeInTheDocument()
    const query = api.GET.mock.calls.find(([path]) => path.endsWith("/lignes"))![1]
      .params.query
    expect(query).toMatchObject({ page: 1, page_size: 500, afficher: "avalider" })
  })

  it("validates the ligne under the cursor with A and moves to the next ligne", async () => {
    const api = setup()
    await waitFor(() => expect(row("1:url")).toBeInTheDocument())

    fireEvent.click(row("1:url"))
    fireEvent.keyDown(window, { key: "a" })

    await waitFor(() =>
      expect(within(row("1:url")).getByText("Validé")).toBeInTheDocument(),
    )
    expect(row("2:url")).toHaveClass("cur")
    expect(api.POST).toHaveBeenCalledWith(
      "/api/suggestions/groupes/{groupe_id}/lignes/decision",
      {
        params: { path: { groupe_id: 1 } },
        body: {
          cles: ["1:url"],
          action: "validate",
          expected_modifie_le: "2026-10-09T10:00:00.000Z",
        },
      },
    )
  })

  it("does not refuse with R, but opens the detail of the groupe with Enter", async () => {
    const api = setup()
    await waitFor(() => expect(row("2:url")).toBeInTheDocument())

    fireEvent.click(row("2:url"))
    fireEvent.keyDown(window, { key: "r" })
    expect(api.POST).not.toHaveBeenCalled()
    expect(screen.queryByText("Refuser le groupe")).toBeNull()

    fireEvent.keyDown(window, { key: "Enter" })
    await waitFor(() => expect(window.location.search).toBe("?vue=lignes&groupe=2"))
  })

  it("chains quick decisions on a same groupe without conflict", async () => {
    let answered = 0
    const api = fakeApi((path, _options, method) => {
      if (method !== "GET") {
        answered += 1
        return { ...groupe(1), modifie_le: `2026-10-09T10:00:0${answered}.000Z` }
      }
      if (path.endsWith("/stats")) return STATS
      if (path.endsWith("/taches")) return []
      if (path.endsWith("/champs/choix")) return {}
      if (path.endsWith("/revue/filtres")) return { champs: [] }
      if (path.endsWith("/lignes")) return LIGNES
      return COHORTE
    })
    renderApp(<CohorteScreen cohorteId={7} />, {
      api,
      url: "/data/revue/cohortes/7?vue=lignes",
    })
    await waitFor(() => expect(row("1:nom")).toBeInTheDocument())

    fireEvent.click(row("1:nom"))
    fireEvent.keyDown(window, { key: "a" })
    fireEvent.keyDown(window, { key: "a" })

    await waitFor(() => expect(api.POST).toHaveBeenCalledTimes(2))
    const expected = api.POST.mock.calls.map(
      ([, options]) => options.body.expected_modifie_le,
    )
    // The second write waits for the first one and sends its answer
    expect(expected).toEqual(["2026-10-09T10:00:00.000Z", "2026-10-09T10:00:01.000Z"])
  })

  describe("lignes par acteur", () => {
    const cible = (id: string) => ({
      identifiant_unique: id,
      nom: `Nom ${id}`,
      ville: "PARIS",
      suggestion_modele: "RevisionActeur",
      admin_urls: {
        importe: `/admin/qfdmo/acteur/${id}/change/`,
        affiche: null,
        corrige: null,
        parent: null,
      },
    })
    const villeLigne = (id: string) =>
      ligne(5, ["ville"], {
        key: `5:${id}:ville`,
        cible: cible(id),
        capacites: { ...ligne(5, ["ville"]).capacites, refuser: true },
      })
    const VILLES = groupe(5, {
      acteur: { ...groupe(5).acteur, nom: "", identifiant_unique: "" },
      libelle: "ville actuel(le) : PARIS · ville proposé(e) : Paris",
      lignes: [villeLigne("A1"), villeLigne("A2"), villeLigne("A3")],
      lignes_validees: 1,
      lignes_refusees: 1,
      lignes_total: 4,
    })
    const COHORTE_VILLES = {
      ...COHORTE,
      policy: {
        ...COHORTE.policy,
        type_action: "ENRICH_ACTEURS_VILLES_TYPO",
        can_reject_line: true,
        lignes_par_acteur: true,
        editable_models: [],
        onglets: [],
      },
    }

    function setupVilles(
      vue: "lignes" | "groupes",
      policy: Partial<typeof COHORTE_VILLES.policy> = {},
    ) {
      const api = fakeApi((path, _options, method) => {
        if (method !== "GET") {
          return {
            ...VILLES,
            lignes: VILLES.lignes.map((l) =>
              l.key === "5:A1:ville" ? { ...l, statut: "REJETEE" } : l,
            ),
          }
        }
        if (path.endsWith("/stats")) return STATS
        if (path.endsWith("/taches")) return []
        if (path.endsWith("/champs/choix")) return {}
        if (path.endsWith("/revue/filtres")) return { champs: [] }
        if (path.endsWith("/lignes"))
          return {
            items: VILLES.lignes.map((l) => ({ groupe_id: 5, key: l.key })),
            groupes: [VILLES],
            total: 2,
            page: 1,
            page_size: 500,
          }
        if (path.endsWith("/groupes"))
          return { items: [VILLES], total: 1, page: 1, page_size: 100 }
        return { ...COHORTE_VILLES, policy: { ...COHORTE_VILLES.policy, ...policy } }
      })
      renderApp(<CohorteScreen cohorteId={7} />, {
        api,
        url: `/data/revue/cohortes/7?vue=${vue}`,
      })
      return api
    }

    it("shows the acteur of each ligne and refuses a ligne with R", async () => {
      const api = setupVilles("lignes")
      await waitFor(() => expect(row("5:A1:ville")).toBeInTheDocument())

      expect(within(row("5:A1:ville")).getAllByText("Nom A1").length).toBeGreaterThan(0)
      fireEvent.click(row("5:A1:ville"))
      fireEvent.keyDown(window, { key: "r" })

      await waitFor(() =>
        expect(api.POST).toHaveBeenCalledWith(
          "/api/suggestions/groupes/{groupe_id}/lignes/decision",
          {
            params: { path: { groupe_id: 5 } },
            body: {
              cles: ["5:A1:ville"],
              action: "reject",
              expected_modifie_le: "2026-10-09T10:00:00.000Z",
            },
          },
        ),
      )
      expect(row("5:A2:ville")).toHaveClass("cur")
    })

    it("hides the parent columns when the policy has none (codes postaux)", async () => {
      setupVilles("groupes", { colonne_parent: false })
      await waitFor(() => expect(row("5:A2:ville")).toBeInTheDocument())

      expect(screen.queryByText("Parent")).not.toBeInTheDocument()
      expect(screen.queryByTitle("Reporter vers le parent")).not.toBeInTheDocument()
      expect(document.querySelector("table.cmp")).toHaveClass("sans-parent")
      expect(row("5:A2:ville").querySelector(".c-par")).toBeNull()
    })

    it("offers to refuse each ligne in the Groupes view", async () => {
      const api = setupVilles("groupes")
      await waitFor(() => expect(row("5:A2:ville")).toBeInTheDocument())

      expect(screen.getByText(/ville actuel\(le\) : PARIS/)).toBeInTheDocument()
      // No modal for these cohortes; the champs column (with the acteur) is wider
      expect(screen.queryByText("Localisation")).not.toBeInTheDocument()
      expect(screen.queryByText("Annuaire entreprise")).not.toBeInTheDocument()
      expect(document.querySelector("table.cmp")).toHaveClass("par-acteur")
      // No correction nor parent of its own for a groupe of several acteurs
      const header = document.querySelector('[data-cursor="g:5"]') as HTMLElement
      expect(within(header).queryByText("pas de correction existante")).toBeNull()
      expect(within(header).queryByText("pas de parent")).toBeNull()
      expect(screen.getByText("Parent")).toBeInTheDocument()
      // Decided lignes (validated + refused) out of the lignes of the groupe
      const progress = within(
        document.querySelector('[data-cursor="g:5"]') as HTMLElement,
      ).getByText("2/4")
      expect(progress).toHaveAttribute(
        "title",
        "1 ligne validée, 1 refusée, 2 à valider",
      )
      expect(progress.querySelector(".bg-ok")).toHaveStyle({ width: "25%" })
      expect(progress.querySelector(".bg-danger")).toHaveStyle({ width: "25%" })
      fireEvent.click(within(row("5:A2:ville")).getByText("Refuser la ligne"))

      await waitFor(() =>
        expect(api.POST.mock.calls.at(-1)![1].body).toMatchObject({
          cles: ["5:A2:ville"],
          action: "reject",
        }),
      )
    })
  })
})
