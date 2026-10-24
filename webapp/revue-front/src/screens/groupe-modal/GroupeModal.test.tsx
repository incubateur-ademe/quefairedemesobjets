import { fireEvent, screen, waitFor, within } from "@testing-library/react"

import { Marker } from "../../__mocks__/maplibre"
import type { GroupeDetail } from "../../api/types"
import { fakeApi, renderApp } from "../../test-utils"
import { CohorteScreen } from "../cohorte/CohorteScreen"
import { COHORTE, groupe, ligne, page, STATS } from "../cohorte/fixtures"

const detail = (): GroupeDetail => ({
  ...groupe(1, {
    lignes: [
      ligne(1, ["nom"]),
      ligne(1, ["latitude", "longitude"], {
        correction: { actuel: null, propose: null, etat: "pas_de_correction" },
      }),
    ],
  }),
  localisation: {
    ligne: "1:latitude,longitude",
    creer_correction: false,
    points: [
      { key: "Origin", latitude: 45.7, longitude: 4.8, draggable: false },
      { key: "Acteur", latitude: 45.71, longitude: 4.81, draggable: false },
      { key: "RevisionActeur", latitude: 45.72, longitude: 4.82, draggable: true },
    ],
  },
  annuaire: {
    siret: [
      {
        source: "corrige",
        label: "Valeur corrigée (acteur affiché)",
        valeur: "12345678900012",
        propose: false,
      },
      {
        source: "acteur",
        label: "Acteur importé",
        valeur: "12345678900013",
        propose: true,
      },
    ],
    siren: [
      {
        source: "corrige",
        label: "Valeur corrigée (acteur affiché)",
        valeur: "123456789",
        propose: false,
      },
    ],
  },
})

type Query = { params: { query: { champ: string; valeur: string } } }

/** Fake Annuaire des entreprises: the SIRET of the source is unknown. */
function annuaireAnswer(options: unknown) {
  const { champ, valeur } = (options as Query).params.query
  if (valeur === "12345678900013") {
    return { trouve: false, entreprise: null, etablissement: null }
  }
  return {
    trouve: true,
    entreprise: {
      siren: "123456789",
      nom: "RESSOURCERIE SA",
      adresse: "1 RUE DE LA PAIX 75001 PARIS",
      activite_code: "47.79Z",
      etat: "inactif",
    },
    etablissement:
      champ === "siret"
        ? {
            siret: valeur,
            nom: "BOUTIQUE",
            adresse: "2 RUE DE LA PAIX 75001 PARIS",
            activite_code: "47.79Z",
            etat: "ferme",
            est_siege: false,
            latitude: 45.75,
            longitude: 4.85,
          }
        : null,
  }
}

function setup(url: string, groupeDetail: GroupeDetail = detail()) {
  const api = fakeApi((path, options, method) => {
    if (method !== "GET") return groupe(1)
    if (path.endsWith("/stats")) return STATS
    if (path.endsWith("/revue/filtres")) return { champs: [] }
    if (path.endsWith("/groupes")) return page([groupe(1), groupe(2)])
    if (path === "/api/suggestions/groupes/{groupe_id}") return groupeDetail
    if (path === "/api/suggestions/annuaire-entreprises") return annuaireAnswer(options)
    return COHORTE
  })
  renderApp(<CohorteScreen cohorteId={7} />, { api, url })
  return api
}

const dialog = () => document.querySelector("wa-dialog") as HTMLElement

describe("GroupeModal", () => {
  beforeEach(() => {
    Marker.instances = []
  })

  it("opens the groupe under the cursor with Enter", async () => {
    setup("/data/revue/cohortes/7")
    await screen.findByText("Acteur 1")

    fireEvent.click(document.querySelector('[data-cursor="g:2"]')!)
    fireEvent.keyDown(window, { key: "Enter" })

    await waitFor(() => expect(window.location.search).toBe("?groupe=2"))
    expect(dialog()).toHaveAttribute("open")
  })

  it("opens a tab from the groupe header and keeps it in the URL", async () => {
    setup("/data/revue/cohortes/7")
    await screen.findByText("Acteur 1")

    const header = document.querySelector('[data-cursor="g:1"]') as HTMLElement
    fireEvent.click(within(header).getByText("Annuaire entreprise"))

    await waitFor(() =>
      expect(window.location.search).toBe("?groupe=1&onglet=annuaire"),
    )
    const modal = dialog()
    // Entreprise of the SIRET and of the SIREN
    await waitFor(() =>
      expect(within(modal).getAllByText("RESSOURCERIE SA")).toHaveLength(2),
    )
    expect(within(modal).getByText("BOUTIQUE")).toBeInTheDocument()
    expect(within(modal).getByText("fermé")).toHaveClass("ae-ferme")
    expect(within(modal).getAllByText("inactif")[0]).toHaveClass("ae-ferme")
    expect(
      within(modal).getAllByText(/Commerce de détail de biens d'occasion en magasin/),
    ).not.toHaveLength(0)
    // Each value says where it comes from
    expect(within(modal).getAllByText("Valeur corrigée (acteur affiché)")).toHaveLength(
      2,
    )
    expect(
      within(modal).getByText("Acteur importé", { selector: ".ae-source" }),
    ).toBeInTheDocument()
    expect(within(modal).getByText("proposé")).toBeInTheDocument()
    expect(
      within(modal).getByText("Introuvable dans l’Annuaire des entreprises"),
    ).toBeInTheDocument()
    expect(
      within(modal).getAllByText("voir dans AE ↗")[0].closest("a"),
    ).toHaveAttribute(
      "href",
      "https://annuaire-entreprises.data.gouv.fr/etablissement/12345678900012",
    )
  })

  it("saves the position of a marker as soon as it is released", async () => {
    const api = setup("/data/revue/cohortes/7?groupe=1&onglet=localisation")
    await screen.findByText("Légende")

    const markers = Marker.instances
    expect(markers.map((m) => m.options.element.dataset.markerKey)).toEqual([
      "Origin",
      "Acteur",
      "RevisionActeur",
    ])
    expect(markers.map((m) => Boolean(m.options.draggable))).toEqual([
      false,
      false,
      true,
    ])
    expect(within(dialog()).getByText("absent")).toBeInTheDocument()

    markers[2].dragTo(45.123456789, 4.987654321)

    await waitFor(() =>
      expect(api.PUT).toHaveBeenCalledWith(
        "/api/suggestions/groupes/{groupe_id}/propositions",
        {
          params: { path: { groupe_id: 1 } },
          body: {
            suggestion_modele: "RevisionActeur",
            champs: ["latitude", "longitude"],
            valeurs: { latitude: "45.123457", longitude: "4.987654" },
            expected_modifie_le: "2026-10-09T10:00:00.000Z",
          },
        },
      ),
    )
  })

  it("does not decide with the keyboard while the modal is open", async () => {
    const api = setup("/data/revue/cohortes/7?groupe=1")
    await screen.findByText("Acteur 1")

    fireEvent.keyDown(window, { key: "a" })

    expect(api.POST).not.toHaveBeenCalled()
  })

  it("creates a correction of the localisation where the source puts it", async () => {
    const base = detail()
    const api = setup("/data/revue/cohortes/7?groupe=1&onglet=localisation", {
      ...base,
      lignes: [ligne(1, ["nom"])],
      localisation: {
        ligne: null,
        creer_correction: true,
        points: base.localisation.points.filter((p) => p.key !== "RevisionActeur"),
      },
    })
    await screen.findByText("Légende")

    fireEvent.click(screen.getByText("Ajouter une correction de la localisation"))

    await waitFor(() =>
      expect(api.PUT).toHaveBeenCalledWith(
        "/api/suggestions/groupes/{groupe_id}/propositions",
        expect.objectContaining({
          body: expect.objectContaining({
            suggestion_modele: "RevisionActeur",
            champs: ["latitude", "longitude"],
            valeurs: { latitude: "45.710000", longitude: "4.810000" },
          }),
        }),
      ),
    )
  })

  it("shows the localisation of the établissement in the Annuaire", async () => {
    const api = setup("/data/revue/cohortes/7?groupe=1&onglet=localisation")
    await screen.findByText("Légende")
    expect(
      screen.queryByText("Établissement dans l’Annuaire des entreprises"),
    ).toBeNull()

    fireEvent.click(screen.getByText("Localisation Annuaire des entreprises"))

    expect(
      await screen.findByText("Établissement dans l’Annuaire des entreprises"),
    ).toBeInTheDocument()
    expect(await screen.findByText("45.750000, 4.850000")).toBeInTheDocument()
    expect(
      within(document.querySelector(".legend-map") as HTMLElement).getByText(
        "2 RUE DE LA PAIX 75001 PARIS",
      ),
    ).toBeInTheDocument()
    expect(api.GET).toHaveBeenCalledWith("/api/suggestions/annuaire-entreprises", {
      params: { query: { champ: "siret", valeur: "12345678900012" } },
    })
    await waitFor(() =>
      expect(
        Marker.instances.some(
          (m) => m.options.element.dataset.markerKey === "AnnuaireEntreprises",
        ),
      ).toBe(true),
    )
  })

  it("offers to add a localisation to an existing correction", async () => {
    const base = detail()
    const api = setup("/data/revue/cohortes/7?groupe=1&onglet=localisation", {
      ...base,
      localisation: { ...base.localisation, creer_correction: true },
    })
    await screen.findByText("Légende")

    fireEvent.click(screen.getByText("Ajouter une correction de la localisation"))

    // Starts from the current localisation of the correction
    await waitFor(() =>
      expect(api.PUT).toHaveBeenCalledWith(
        "/api/suggestions/groupes/{groupe_id}/propositions",
        expect.objectContaining({
          body: expect.objectContaining({
            valeurs: { latitude: "45.720000", longitude: "4.820000" },
          }),
        }),
      ),
    )
  })

  it("shows a marker above the others when clicking it or its legend", async () => {
    setup("/data/revue/cohortes/7?groupe=1&onglet=localisation")
    await screen.findByText("Légende")
    const element = (key: string) =>
      Marker.instances.find((m) => m.options.element.dataset.markerKey === key)!.options
        .element

    fireEvent.click(
      screen.getByText("Acteur importé après application de la modification"),
    )

    expect(element("Acteur").style.zIndex).toBe("10")
    expect(element("Origin").style.zIndex).toBe("")
    expect(
      screen
        .getByText("Acteur importé après application de la modification")
        .closest(".legend-map__item"),
    ).toHaveAttribute("aria-pressed", "true")

    fireEvent.click(element("Origin"))

    expect(element("Origin").style.zIndex).toBe("10")
    expect(element("Acteur").style.zIndex).toBe("")
    expect(element("Origin")).toHaveClass("pin--focused")
  })
})
