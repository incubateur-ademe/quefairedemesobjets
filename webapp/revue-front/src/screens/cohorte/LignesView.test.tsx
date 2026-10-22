import { fireEvent, screen, waitFor, within } from "@testing-library/react"

import type { LignePage } from "../../api/types"
import { fakeApi, renderApp } from "../../test-utils"
import { CohorteScreen } from "./CohorteScreen"
import { COHORTE, groupe, STATS } from "./fixtures"

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
          champs: [["url"]],
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
})
